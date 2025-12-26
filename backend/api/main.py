from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from backend.core.models import Faculty, CourseActivity, ProblemInstance, OptimizationResult
from backend.data.generator import DataGenerator
from backend.solvers.ortools_solver import ORToolsSolver
from backend.solvers.pulp_solver import PuLPSolver
from backend.solvers.genetic_solver import GeneticSolver
from backend.solvers.sa_solver import SimulatedAnnealingSolver

app = FastAPI(
    title="Teaching Load Distribution API",
    description="API for optimizing teaching load assignments",
    version="1.0.0"
)

# In-memory storage for demo purposes
# In production, this would be a database
instances = {}
results = {}

class InstanceCreateRequest(BaseModel):
    size: str = "small"
    seed: int = 42

class SolveRequest(BaseModel):
    instance_id: str
    solver: str = "ortools"  # ortools, pulp, genetic, sa
    time_limit: int = 300

@app.get("/")
def read_root():
    return {"message": "Welcome to Teaching Load Optimization API"}

@app.post("/instances/generate")
def generate_instance(request: InstanceCreateRequest):
    generator = DataGenerator(seed=request.seed)
    try:
        instance = generator.generate_instance(request.size)
        instance_id = f"{request.size}_{request.seed}"
        instances[instance_id] = instance
        return {
            "instance_id": instance_id,
            "summary": {
                "faculty_count": len(instance.faculty),
                "activity_count": len(instance.activities),
                "total_demand": instance.get_total_demand(),
                "total_capacity": instance.get_total_capacity()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/solve")
def solve_instance(request: SolveRequest):
    if request.instance_id not in instances:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    instance = instances[request.instance_id]
    
    solver = None
    if request.solver == "ortools":
        solver = ORToolsSolver(time_limit_seconds=request.time_limit)
    elif request.solver == "pulp":
        solver = PuLPSolver(time_limit_seconds=request.time_limit)
    elif request.solver == "genetic":
        solver = GeneticSolver(time_limit_seconds=request.time_limit)
    elif request.solver == "sa":
        solver = SimulatedAnnealingSolver(time_limit_seconds=request.time_limit)
    else:
        raise HTTPException(status_code=400, detail="Invalid solver type")
    
    result = solver.solve(instance)
    
    result_id = f"{request.instance_id}_{request.solver}"
    results[result_id] = result
    
    return {
        "result_id": result_id,
        "status": result.solver_status,
        "is_feasible": result.is_feasible,
        "total_deviation": result.total_deviation,
        "computation_time": result.computation_time
    }

@app.get("/results/{result_id}")
def get_result(result_id: str):
    if result_id not in results:
        raise HTTPException(status_code=404, detail="Result not found")
    
    result = results[result_id]
    return result
