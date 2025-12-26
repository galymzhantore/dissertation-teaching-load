"""
Simulated Annealing solver for teaching load distribution.

This module implements a metaheuristic approach using Simulated Annealing
to find near-optimal solutions for the teaching load distribution problem.
"""

import time
import random
import math
import copy
from typing import List, Dict, Tuple
import numpy as np

from backend.core.models import (
    ProblemInstance, OptimizationResult, Assignment
)


class SimulatedAnnealingSolver:
    """
    Teaching load distribution solver using Simulated Annealing.
    
    Attributes:
        initial_temp: Starting temperature
        cooling_rate: Rate at which temperature decreases
        min_temp: Minimum temperature to stop
        steps_per_temp: Number of iterations at each temperature
        time_limit: Maximum time allowed in seconds
    """
    
    def __init__(
        self, 
        initial_temp: float = 1000.0,
        cooling_rate: float = 0.95,
        min_temp: float = 0.1,
        steps_per_temp: int = 100,
        time_limit_seconds: int = 300
    ):
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.steps_per_temp = steps_per_temp
        self.time_limit = time_limit_seconds
        
    def solve(self, instance: ProblemInstance) -> OptimizationResult:
        """
        Solve the problem using Simulated Annealing.
        """
        start_time = time.time()
        
        # Pre-process: Map activities to qualified faculty indices
        activity_options = {}
        faculty_map = {f.id: i for i, f in enumerate(instance.faculty)}
        faculty_ids = [f.id for f in instance.faculty]
        
        for i, activity in enumerate(instance.activities):
            qualified = []
            for f in instance.faculty:
                if instance.qualification_matrix.get((f.id, activity.id), False):
                    qualified.append(faculty_map[f.id])
            
            if not qualified:
                return OptimizationResult(
                    assignments=[],
                    objective_value=float('inf'),
                    total_deviation=float('inf'),
                    computation_time=time.time() - start_time,
                    solver_name="Simulated Annealing",
                    solver_status="INFEASIBLE",
                    faculty_loads={},
                    unassigned_activities=[activity.id],
                    is_feasible=False
                )
            activity_options[i] = qualified
            
        # Initial solution (Random)
        current_solution = self._generate_random_solution(instance, activity_options)
        current_energy = self._calculate_energy(current_solution, instance, faculty_ids)
        
        best_solution = list(current_solution)
        best_energy = current_energy
        
        temp = self.initial_temp
        
        # Annealing loop
        while temp > self.min_temp:
            # Check time limit
            if time.time() - start_time > self.time_limit:
                break
                
            for _ in range(self.steps_per_temp):
                # Generate neighbor
                neighbor = list(current_solution)
                self._mutate(neighbor, activity_options)
                
                neighbor_energy = self._calculate_energy(neighbor, instance, faculty_ids)
                
                # Acceptance probability
                delta_energy = neighbor_energy - current_energy
                
                if delta_energy < 0:
                    # Improvement: always accept
                    current_solution = neighbor
                    current_energy = neighbor_energy
                    
                    if current_energy < best_energy:
                        best_solution = list(current_solution)
                        best_energy = current_energy
                else:
                    # Worse solution: accept with probability
                    prob = math.exp(-delta_energy / temp)
                    if random.random() < prob:
                        current_solution = neighbor
                        current_energy = neighbor_energy
            
            # Cool down
            temp *= self.cooling_rate
            
        # Final evaluation
        computation_time = time.time() - start_time
        
        # Convert best solution to result
        assignments = []
        faculty_loads = {fid: 0.0 for fid in faculty_ids}
        
        for i, faculty_idx in enumerate(best_solution):
            activity = instance.activities[i]
            faculty_id = faculty_ids[faculty_idx]
            
            faculty = instance.faculty[faculty_idx]
            preference = faculty.preferences.get(activity.id, 0)
            
            assignments.append(Assignment(
                faculty_id=faculty_id,
                activity_id=activity.id,
                preference_score=preference
            ))
            
            faculty_loads[faculty_id] += activity.hours
            
        # Calculate final deviation
        total_dev = sum(
            abs(faculty_loads[f.id] - f.target_load)
            for f in instance.faculty
        )
        
        # Check max load constraints
        is_feasible = True
        for f in instance.faculty:
            if faculty_loads[f.id] > f.max_load:
                is_feasible = False
                break
                
        return OptimizationResult(
            assignments=assignments,
            objective_value=best_energy,
            total_deviation=total_dev,
            computation_time=computation_time,
            solver_name="Simulated Annealing",
            solver_status="COMPLETED",
            faculty_loads=faculty_loads,
            is_feasible=is_feasible
        )

    def _generate_random_solution(self, instance, activity_options):
        solution = []
        num_activities = len(instance.activities)
        for i in range(num_activities):
            options = activity_options[i]
            solution.append(random.choice(options))
        return solution

    def _calculate_energy(self, solution, instance, faculty_ids):
        """
        Calculate energy (lower is better).
        Energy = Weighted Deviation + Penalty for Overload - Preference Score
        """
        loads = {fid: 0.0 for fid in faculty_ids}
        total_preference = 0
        penalty = 0.0
        
        for i, faculty_idx in enumerate(solution):
            activity = instance.activities[i]
            faculty_id = faculty_ids[faculty_idx]
            loads[faculty_id] += activity.hours
            
            # Add preference score
            faculty = instance.faculty[faculty_idx]
            total_preference += faculty.preferences.get(activity.id, 0)
            
        total_weighted_deviation = 0.0
        
        for i, f in enumerate(instance.faculty):
            load = loads[f.id]
            deviation = abs(load - f.target_load)
            total_weighted_deviation += deviation * f.weight
            
            # Penalty for exceeding max load
            if load > f.max_load:
                penalty += (load - f.max_load) * 100  # Heavy penalty
        
        # We want to maximize preference, so we subtract it from the minimization objective
        preference_impact = total_preference * 0.5
        
        return total_weighted_deviation + penalty - preference_impact

    def _mutate(self, solution, activity_options):
        # Randomly reassign one activity
        idx = random.randint(0, len(solution)-1)
        options = activity_options[idx]
        solution[idx] = random.choice(options)


if __name__ == "__main__":
    from backend.data.generator import DataGenerator
    
    print("="*60)
    print("Testing Simulated Annealing Solver")
    print("="*60)
    
    generator = DataGenerator(seed=42)
    instance = generator.generate_instance("small")
    
    solver = SimulatedAnnealingSolver(time_limit_seconds=10)
    print("\nSolving...")
    
    result = solver.solve(instance)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result.solver_status}")
    print(f"Feasible: {result.is_feasible}")
    print(f"Computation time: {result.computation_time:.2f}s")
    print(f"Total deviation: {result.total_deviation:.1f} hours")
