import time
from typing import Dict, List
import pulp

from backend.core.models import (
    ProblemInstance, OptimizationResult, Assignment
)


class PuLPSolver:
    def __init__(self, time_limit_seconds: int = 300, solver_name: str = "PULP_CBC_CMD"):
        self.time_limit = time_limit_seconds
        self.solver_name = solver_name
        self.prob = None
        
    def solve(self, instance: ProblemInstance) -> OptimizationResult:
        start_time = time.time()
        
        self.prob = pulp.LpProblem("Teaching_Load_Distribution", pulp.LpMinimize)
        
        x = {}
        for faculty in instance.faculty:
            for activity in instance.activities:
                if instance.qualification_matrix.get((faculty.id, activity.id), False):
                    var_name = f"x_f{faculty.id}_a{activity.id}"
                    x[(faculty.id, activity.id)] = pulp.LpVariable(
                        var_name, cat='Binary'
                    )
        
        faculty_loads = {}
        for faculty in instance.faculty:
            var_name = f"load_f{faculty.id}"
            faculty_loads[faculty.id] = pulp.LpVariable(
                var_name, lowBound=0, upBound=faculty.max_load
            )
        
        deviations = {}
        for faculty in instance.faculty:
            var_name = f"dev_f{faculty.id}"
            deviations[faculty.id] = pulp.LpVariable(
                var_name, lowBound=0, upBound=faculty.max_load
            )
        
        for activity in instance.activities:
            qualified_assignments = [
                x[(f.id, activity.id)]
                for f in instance.faculty
                if (f.id, activity.id) in x
            ]
            
            if not qualified_assignments:
                print(f"⚠️  Warning: No qualified faculty for {activity.id}")
                continue
            
            self.prob += (
                pulp.lpSum(qualified_assignments) == 1,
                f"assign_activity_{activity.id}"
            )
        
        for faculty in instance.faculty:
            assigned_hours = []
            for activity in instance.activities:
                if (faculty.id, activity.id) in x:
                    assigned_hours.append(
                        x[(faculty.id, activity.id)] * activity.hours
                    )
            
            if assigned_hours:
                self.prob += (
                    faculty_loads[faculty.id] == pulp.lpSum(assigned_hours),
                    f"load_calculation_f{faculty.id}"
                )
            else:
                self.prob += (
                    faculty_loads[faculty.id] == 0,
                    f"load_zero_f{faculty.id}"
                )
        
        for faculty in instance.faculty:
            self.prob += (
                faculty_loads[faculty.id] <= faculty.max_load,
                f"max_load_f{faculty.id}"
            )
        
        for faculty in instance.faculty:
            self.prob += (
                deviations[faculty.id] >= faculty_loads[faculty.id] - faculty.target_load,
                f"dev_pos_f{faculty.id}"
            )
            self.prob += (
                deviations[faculty.id] >= faculty.target_load - faculty_loads[faculty.id],
                f"dev_neg_f{faculty.id}"
            )
        
        objective_terms = [
            faculty.weight * deviations[faculty.id]
            for faculty in instance.faculty
        ]
        self.prob += pulp.lpSum(objective_terms)
        
        if self.solver_name == "PULP_CBC_CMD":
            solver = pulp.PULP_CBC_CMD(
                timeLimit=self.time_limit,
                msg=0,
                threads=4,
                gapRel=0.01,
                presolve=True,
                cuts=True,
                strong=5
            )
        elif self.solver_name == "GLPK_CMD":
            solver = pulp.GLPK_CMD(
                timeLimit=self.time_limit,
                msg=0
            )
        else:
            solver = pulp.PULP_CBC_CMD(timeLimit=self.time_limit, msg=0)
        
        status = self.prob.solve(solver)
        computation_time = time.time() - start_time
        
        if status == pulp.LpStatusOptimal or status == pulp.LpStatusNotSolved:
            if pulp.value(self.prob.objective) is not None:
                assignments = []
                actual_loads = {}
                
                for faculty in instance.faculty:
                    total_load = 0
                    for activity in instance.activities:
                        if (faculty.id, activity.id) in x:
                            if pulp.value(x[(faculty.id, activity.id)]) > 0.5:
                                preference = faculty.preferences.get(activity.id, 0)
                                assignments.append(Assignment(
                                    faculty_id=faculty.id,
                                    activity_id=activity.id,
                                    preference_score=preference
                                ))
                                total_load += activity.hours
                    
                    actual_loads[faculty.id] = total_load
                
                total_dev = sum(
                    abs(actual_loads.get(f.id, 0) - f.target_load)
                    for f in instance.faculty
                )
                
                status_str = "OPTIMAL" if status == pulp.LpStatusOptimal else "FEASIBLE"
                
                return OptimizationResult(
                    assignments=assignments,
                    objective_value=pulp.value(self.prob.objective),
                    total_deviation=total_dev,
                    computation_time=computation_time,
                    solver_name=f"PuLP ({self.solver_name})",
                    solver_status=status_str,
                    faculty_loads=actual_loads,
                    is_feasible=True,
                    gap=None
                )
        
        status_names = {
            pulp.LpStatusInfeasible: "INFEASIBLE",
            pulp.LpStatusUnbounded: "UNBOUNDED",
            pulp.LpStatusNotSolved: "NOT_SOLVED",
            pulp.LpStatusUndefined: "UNDEFINED"
        }
        
        return OptimizationResult(
            assignments=[],
            objective_value=float('inf'),
            total_deviation=float('inf'),
            computation_time=computation_time,
            solver_name=f"PuLP ({self.solver_name})",
            solver_status=status_names.get(status, "ERROR"),
            faculty_loads={},
            unassigned_activities=[a.id for a in instance.activities],
            is_feasible=False
        )


if __name__ == "__main__":
    from backend.data.generator import DataGenerator
    
    print("="*60)
    print("Testing PuLP Solver")
    print("="*60)
    
    generator = DataGenerator(seed=42)
    instance = generator.generate_instance("small")
    
    print(f"\nProblem: {instance.name}")
    print(f"Faculty: {len(instance.faculty)}")
    print(f"Activities: {len(instance.activities)}")
    print(f"Total demand: {instance.get_total_demand()} hours")
    print(f"Total capacity: {instance.get_total_capacity()} hours")
    
    solver = PuLPSolver(time_limit_seconds=60)
    print("\nSolving with PuLP...")
    
    result = solver.solve(instance)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result.solver_status}")
    print(f"Feasible: {result.is_feasible}")
    print(f"Computation time: {result.computation_time:.2f}s")
    print(f"Assignments made: {len(result.assignments)}")
    print(f"Total deviation: {result.total_deviation:.1f} hours")
    
    if result.is_feasible:
        target_loads = {f.id: f.target_load for f in instance.faculty}
        metrics = result.get_equity_metrics(target_loads)
        print(f"\nEquity Metrics:")
        print(f"  Mean deviation: {metrics['mean_deviation']:.1f} hours")
        print(f"  Max deviation: {metrics['max_deviation']:.1f} hours")
        print(f"  Std deviation: {metrics['std_deviation']:.1f}")
