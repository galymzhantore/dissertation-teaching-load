"""
Experiment runner for comparing different solvers.
"""

import time
import pandas as pd
from typing import List, Dict, Type
import matplotlib.pyplot as plt
import seaborn as sns
import os

from backend.core.models import ProblemInstance, OptimizationResult
from backend.data.generator import DataGenerator
from backend.solvers.ortools_solver import ORToolsSolver
from backend.solvers.pulp_solver import PuLPSolver
from backend.solvers.genetic_solver import GeneticSolver
from backend.solvers.sa_solver import SimulatedAnnealingSolver

class ExperimentRunner:
    def __init__(self, output_dir: str = "data/results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def run_comparison(
        self, 
        sizes: List[str] = ["small", "medium"], 
        seeds: List[int] = [42],
        solvers: List[str] = ["ortools", "pulp", "genetic", "sa"],
        time_limit: int = 60
    ) -> pd.DataFrame:
        """
        Run comparison experiments.
        """
        results_data = []
        
        for size in sizes:
            for seed in seeds:
                print(f"\nGenerating {size} instance (seed={seed})...")
                generator = DataGenerator(seed=seed)
                instance = generator.generate_instance(size)
                
                # Calculate instance complexity metrics
                complexity = {
                    "size": size,
                    "seed": seed,
                    "faculty": len(instance.faculty),
                    "activities": len(instance.activities),
                    "constraints": len(instance.activities) + len(instance.faculty), # Approx
                    "vars": len(instance.faculty) * len(instance.activities) # Approx
                }
                
                for solver_name in solvers:
                    print(f"  Running {solver_name}...", end=" ", flush=True)
                    
                    solver = self._get_solver(solver_name, time_limit)
                    
                    try:
                        result = solver.solve(instance)
                        
                        # Calculate additional metrics
                        target_loads = {f.id: f.target_load for f in instance.faculty}
                        equity = result.get_equity_metrics(target_loads) if result.is_feasible else {}
                        
                        row = {
                            **complexity,
                            "solver": result.solver_name,
                            "status": result.solver_status,
                            "feasible": result.is_feasible,
                            "time_sec": result.computation_time,
                            "total_deviation": result.total_deviation,
                            "mean_deviation": equity.get("mean_deviation", float('inf')),
                            "max_deviation": equity.get("max_deviation", float('inf')),
                            "objective": result.objective_value
                        }
                        results_data.append(row)
                        print(f"Done ({result.computation_time:.2f}s) - Dev: {result.total_deviation:.1f}")
                        
                    except Exception as e:
                        print(f"Failed: {str(e)}")
                        
        df = pd.DataFrame(results_data)
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = f"{self.output_dir}/comparison_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\nResults saved to {csv_path}")
        
        return df

    def _get_solver(self, name: str, time_limit: int):
        if name == "ortools":
            return ORToolsSolver(time_limit_seconds=time_limit)
        elif name == "pulp":
            return PuLPSolver(time_limit_seconds=time_limit)
        elif name == "genetic":
            return GeneticSolver(
                population_size=100, 
                generations=200, 
                time_limit_seconds=time_limit
            )
        elif name == "sa":
            return SimulatedAnnealingSolver(
                initial_temp=1000, 
                time_limit_seconds=time_limit
            )
        else:
            raise ValueError(f"Unknown solver: {name}")

if __name__ == "__main__":
    runner = ExperimentRunner()
    
    # Run a quick comparison
    df = runner.run_comparison(
        sizes=["small"],
        seeds=[42],
        solvers=["ortools", "genetic", "sa"], # Skip pulp for speed in demo
        time_limit=10
    )
    
    print("\nSummary:")
    print(df[["solver", "time_sec", "total_deviation", "feasible"]].to_string())
