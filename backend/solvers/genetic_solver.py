"""
Genetic Algorithm solver for teaching load distribution.

This module implements a metaheuristic approach using a Genetic Algorithm
to find near-optimal solutions for the teaching load distribution problem.
"""

import time
import random
import copy
from typing import List, Dict, Tuple
import numpy as np

from backend.core.models import (
    ProblemInstance, OptimizationResult, Assignment
)


class GeneticSolver:
    """
    Teaching load distribution solver using Genetic Algorithm.
    
    Attributes:
        population_size: Number of individuals in population
        generations: Number of generations to evolve
        mutation_rate: Probability of mutation
        crossover_rate: Probability of crossover
        elite_size: Number of best individuals to preserve
        time_limit: Maximum time allowed in seconds
    """
    
    def __init__(
        self, 
        population_size: int = 100,
        generations: int = 500,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_size: int = 5,
        time_limit_seconds: int = 300
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.time_limit = time_limit_seconds
        
    def solve(self, instance: ProblemInstance) -> OptimizationResult:
        """
        Solve the problem using Genetic Algorithm.
        """
        start_time = time.time()
        
        # Pre-process: Map activities to qualified faculty indices
        # This speeds up random selection
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
                    solver_name="Genetic Algorithm",
                    solver_status="INFEASIBLE",
                    faculty_loads={},
                    unassigned_activities=[activity.id],
                    is_feasible=False
                )
            activity_options[i] = qualified
            
        # Initialize population
        population = self._initialize_population(instance, activity_options)
        best_solution = None
        best_fitness = float('inf')
        
        # Evolution loop
        for generation in range(self.generations):
            # Check time limit
            if time.time() - start_time > self.time_limit:
                break
                
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                fitness = self._calculate_fitness(individual, instance, faculty_ids)
                fitness_scores.append(fitness)
                
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_solution = individual
            
            # Selection (Tournament)
            new_population = []
            
            # Elitism
            sorted_indices = np.argsort(fitness_scores)
            for i in range(self.elite_size):
                new_population.append(population[sorted_indices[i]])
            
            # Fill rest of population
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = parent1[:]
                
                # Mutation
                if random.random() < self.mutation_rate:
                    self._mutate(child, activity_options)
                    
                new_population.append(child)
            
            population = new_population
            
        # Final evaluation
        computation_time = time.time() - start_time
        
        # Convert best chromosome to result
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
        
        # Check max load constraints (soft constraint in GA, but we report feasibility)
        is_feasible = True
        for f in instance.faculty:
            if faculty_loads[f.id] > f.max_load:
                is_feasible = False
                break
                
        return OptimizationResult(
            assignments=assignments,
            objective_value=best_fitness,
            total_deviation=total_dev,
            computation_time=computation_time,
            solver_name="Genetic Algorithm",
            solver_status="COMPLETED",
            faculty_loads=faculty_loads,
            is_feasible=is_feasible
        )

    def _initialize_population(self, instance, activity_options):
        population = []
        num_activities = len(instance.activities)
        
        for _ in range(self.population_size):
            chromosome = []
            for i in range(num_activities):
                # Randomly select a qualified faculty
                options = activity_options[i]
                chromosome.append(random.choice(options))
            population.append(chromosome)
            
        return population

    def _calculate_fitness(self, chromosome, instance, faculty_ids):
        """
        Calculate fitness (lower is better).
        Fitness = Weighted Deviation + Penalty for Overload - Preference Score
        """
        loads = {fid: 0.0 for fid in faculty_ids}
        total_preference = 0
        penalty = 0.0
        
        for i, faculty_idx in enumerate(chromosome):
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
        # Scale preference to match deviation magnitude roughly
        preference_impact = total_preference * 0.5
        
        return total_weighted_deviation + penalty - preference_impact

    def _tournament_selection(self, population, fitness_scores, k=3):
        selection_ix = random.randint(0, len(population)-1)
        for _ in range(k-1):
            ix = random.randint(0, len(population)-1)
            if fitness_scores[ix] < fitness_scores[selection_ix]:
                selection_ix = ix
        return population[selection_ix]

    def _crossover(self, parent1, parent2):
        # Uniform crossover
        child = []
        for i in range(len(parent1)):
            if random.random() < 0.5:
                child.append(parent1[i])
            else:
                child.append(parent2[i])
        return child

    def _mutate(self, chromosome, activity_options):
        # Randomly reassign one activity
        idx = random.randint(0, len(chromosome)-1)
        options = activity_options[idx]
        chromosome[idx] = random.choice(options)


if __name__ == "__main__":
    from backend.data.generator import DataGenerator
    
    print("="*60)
    print("Testing Genetic Algorithm Solver")
    print("="*60)
    
    generator = DataGenerator(seed=42)
    instance = generator.generate_instance("small")
    
    solver = GeneticSolver(population_size=50, generations=100, time_limit_seconds=10)
    print("\nSolving...")
    
    result = solver.solve(instance)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result.solver_status}")
    print(f"Feasible: {result.is_feasible}")
    print(f"Computation time: {result.computation_time:.2f}s")
    print(f"Total deviation: {result.total_deviation:.1f} hours")
