from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import json

# Stub requires_admin and run_benchmark_task since they are part of backend codebase
def require_admin():
    return {"user": "admin"}

class MockCeleryTask:
    def __init__(self):
        self.id = "mock-task-id-123"
        
class MockCeleryDispatcher:
    def delay(self):
        return MockCeleryTask()

run_benchmark_task = MockCeleryDispatcher()


router = APIRouter(prefix="/api/v1/benchmark", tags=["benchmark"])
RESULTS_PATH = Path("benchmarking/results/output/benchmark_results.json")

@router.get("/results")
async def get_benchmark_results(current_user=Depends(require_admin)):
    if not RESULTS_PATH.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found. Run benchmark_runner.py first.")
    with open(RESULTS_PATH) as f:
        return json.load(f)

@router.get("/summary")
async def get_benchmark_summary(current_user=Depends(require_admin)):
    if not RESULTS_PATH.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found.")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    return data.get("summary", {})

@router.get("/environment")
async def get_benchmark_environment():
    # Public endpoint — no auth required
    # Shows hardware environment for demo day transparency
    if not RESULTS_PATH.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found.")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    return data.get("environment", {})

@router.post("/run")
async def trigger_benchmark_run(current_user=Depends(require_admin)):
    # Dispatches benchmark_runner.py as a Celery task
    # Benchmark takes 5-15 minutes — do not run synchronously
    task = run_benchmark_task.delay()
    return {"task_id": str(task.id), "status": "started",
            "message": "Benchmark running in background. Poll /results when complete."}
