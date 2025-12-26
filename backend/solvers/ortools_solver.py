import time
from typing import Dict, List
from ortools.sat.python import cp_model

from backend.core.models import (
    ProblemInstance, OptimizationResult, Assignment
)


class ORToolsSolver:
    def __init__(self, time_limit_seconds: int = 300):
        self.time_limit = time_limit_seconds
        self.model = None
        self.solver = None
        
    def solve(self, instance: ProblemInstance) -> OptimizationResult:
        start_time = time.time()
        
        self.model = cp_model.CpModel()
        
        x = {}
        for faculty in instance.faculty:
            for activity in instance.activities:
                if instance.qualification_matrix.get((faculty.id, activity.id), False):
                    x[(faculty.id, activity.id)] = self.model.NewBoolVar(
                        f'assign_f{faculty.id}_a{activity.id}'
                    )
        
        faculty_loads = {}
        for faculty in instance.faculty:
            max_possible = int(faculty.max_load * 10)
            faculty_loads[faculty.id] = self.model.NewIntVar(
                0, max_possible, f'load_f{faculty.id}'
            )
        
        deviations = {}
        deviation_pos = {}
        deviation_neg = {}
        
        for faculty in instance.faculty:
            max_dev = int(faculty.max_load * 10)
            deviations[faculty.id] = self.model.NewIntVar(
                0, max_dev, f'deviation_f{faculty.id}'
            )
            deviation_pos[faculty.id] = self.model.NewIntVar(
                0, max_dev, f'dev_pos_f{faculty.id}'
            )
            deviation_neg[faculty.id] = self.model.NewIntVar(
                0, max_dev, f'dev_neg_f{faculty.id}'
            )
        
        for activity in instance.activities:
            qualified_faculty = [
                x[(f.id, activity.id)]
                for f in instance.faculty
                if (f.id, activity.id) in x
            ]
            
            if not qualified_faculty:
                print(f"⚠️  Warning: No qualified faculty for {activity.id}")
                continue
            
            self.model.Add(sum(qualified_faculty) == 1)
        
        for faculty in instance.faculty:
            assigned_hours = []
            for activity in instance.activities:
                if (faculty.id, activity.id) in x:
                    hours_scaled = int(activity.hours * 10)
                    assigned_hours.append(x[(faculty.id, activity.id)] * hours_scaled)
            
            if assigned_hours:
                self.model.Add(faculty_loads[faculty.id] == sum(assigned_hours))
            else:
                self.model.Add(faculty_loads[faculty.id] == 0)
        
        for faculty in instance.faculty:
            max_load_scaled = int(faculty.max_load * 10)
            self.model.Add(faculty_loads[faculty.id] <= max_load_scaled)
        
        for faculty in instance.faculty:
            target_scaled = int(faculty.target_load * 10)
            
            self.model.Add(
                faculty_loads[faculty.id] - target_scaled ==
                deviation_pos[faculty.id] - deviation_neg[faculty.id]
            )
            
            self.model.Add(
                deviations[faculty.id] ==
                deviation_pos[faculty.id] + deviation_neg[faculty.id]
            )
        
        objective_terms = []
        
        for faculty in instance.faculty:
            weight_scaled = int(faculty.weight * 100)
            objective_terms.append(weight_scaled * deviations[faculty.id])
            
        preference_weight = 10
        
        for faculty in instance.faculty:
            for activity in instance.activities:
                if (faculty.id, activity.id) in x:
                    pref = faculty.preferences.get(activity.id, 0)
                    if pref > 0:
                        term = x[(faculty.id, activity.id)] * pref * preference_weight
                        objective_terms.append(-term)
        
        self.model.Minimize(sum(objective_terms))
        
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.time_limit
        self.solver.parameters.log_search_progress = False
        
        status = self.solver.Solve(self.model)
        
        computation_time = time.time() - start_time
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            assignments = []
            actual_loads = {}
            
            for faculty in instance.faculty:
                total_load = 0
                for activity in instance.activities:
                    if (faculty.id, activity.id) in x:
                        if self.solver.Value(x[(faculty.id, activity.id)]) == 1:
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
            
            status_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
            
            return OptimizationResult(
                assignments=assignments,
                objective_value=self.solver.ObjectiveValue() / 1000,
                total_deviation=total_dev,
                computation_time=computation_time,
                solver_name="OR-Tools CP-SAT",
                solver_status=status_str,
                faculty_loads=actual_loads,
                is_feasible=True,
                gap=None if status == cp_model.OPTIMAL else 0.0
            )
        
        else:
            status_names = {
                cp_model.INFEASIBLE: "INFEASIBLE",
                cp_model.MODEL_INVALID: "MODEL_INVALID",
                cp_model.UNKNOWN: "UNKNOWN"
            }
            
            return OptimizationResult(
                assignments=[],
                objective_value=float('inf'),
                total_deviation=float('inf'),
                computation_time=computation_time,
                solver_name="OR-Tools CP-SAT",
                solver_status=status_names.get(status, "ERROR"),
                faculty_loads={},
                unassigned_activities=[a.id for a in instance.activities],
                is_feasible=False
            )


if __name__ == "__main__":
    from backend.data.generator import DataGenerator
    
    print("="*60)
    print("Testing OR-Tools Solver")
    print("="*60)
    
    generator = DataGenerator(seed=42)
    instance = generator.generate_instance("small")
    
    print(f"\nProblem: {instance.name}")
    print(f"Faculty: {len(instance.faculty)}")
    print(f"Activities: {len(instance.activities)}")
    print(f"Total demand: {instance.get_total_demand()} hours")
    print(f"Total capacity: {instance.get_total_capacity()} hours")
    
    solver = ORToolsSolver(time_limit_seconds=60)
    print("\nSolving...")
    
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
        
        print(f"\nSample assignments:")
        for i, assign in enumerate(result.assignments[:5]):
            faculty = next(f for f in instance.faculty if f.id == assign.faculty_id)
            activity = next(a for a in instance.activities if a.id == assign.activity_id)
            print(f"  {faculty.name} → {activity}")
