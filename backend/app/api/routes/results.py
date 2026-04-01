from fastapi import APIRouter, HTTPException, Path
from uuid import UUID
from datetime import datetime, timezone

from app.models.schemas import AnalysisResult

router = APIRouter(tags=["results"])

@router.get("/results/{job_id}", response_model=AnalysisResult)
async def get_results(job_id: UUID = Path(...)):
    # [MOCK] Fetch from DB
    # If status="failed", return error detail (maybe raise HTTPException or just return schema)
    # If status="processing" or "queued", return partial AnalysisResult
    
    # Mocking a processing state
    return AnalysisResult(
        job_id=job_id,
        status="processing",
        created_at=datetime.now(timezone.utc)
    )
