from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from uuid import UUID

from app.models.schemas import AnalysisRequest, JobStatusResponse

router = APIRouter(tags=["analyze"])

class AnalyzeResponse(BaseModel):
    job_id: UUID
    status: str
    message: str

@router.post("/analyze", response_model=AnalyzeResponse)
async def trigger_analysis(request: AnalysisRequest):
    # [MOCK] Validates job_id exists in DB with status="uploaded" or "queued"
    # [MOCK] Dispatches Celery task: run_analysis_pipeline.delay(job_id)
    # [MOCK] Updates DB status to "queued"
    
    return AnalyzeResponse(
        job_id=request.job_id,
        status="queued",
        message="Analysis started"
    )

@router.get("/analyze/status/{job_id}", response_model=JobStatusResponse)
async def get_analysis_status(job_id: UUID = Path(...)):
    # [MOCK] Pull current status + progress_step from Redis
    return JobStatusResponse(
        job_id=job_id,
        status="processing",
        progress_step="face_detection_and_extraction",
        progress_percent=25
    )
