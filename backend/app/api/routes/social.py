import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.auth.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/social", tags=["social"])

# In-memory task store for mock
_scan_tasks: dict[str, dict] = {}


# ─── Request / Response Models ────────────────────────────────────────────────

class ScanURLRequest(BaseModel):
    url: str
    caption: Optional[str] = None


class ScanURLResponse(BaseModel):
    task_id: str
    status: str


class ScanResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


class ReverseSearchResponse(BaseModel):
    similar_images_found: int
    top_matches: list
    recontextualized_flag: bool
    old_image_reposted_flag: bool
    original_source_urls: list


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/scan-url", response_model=ScanURLResponse)
def scan_url(
    body: ScanURLRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a social media post URL for context scanning.
    Runs scan_social_context as a Celery task (can take 15–30s for yt-dlp download).
    Frontend polls GET /scan-result/{task_id} (same pattern as analyze/status).
    """
    task_id = str(uuid.uuid4())

    # Validate URL format
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    # Dispatch Celery task
    try:
        from app.worker import social_scan_task
        celery_task = social_scan_task.delay(body.url, task_id, body.caption)
        _scan_tasks[task_id] = {
            "status": "scanning",
            "celery_task_id": str(celery_task.id),
            "result": None,
        }
    except Exception as e:
        logger.warning(f"Celery dispatch failed, running synchronously: {e}")
        # Fallback: run synchronously for dev/testing
        from app.social.context_scanner import scan_social_context, context_scan_to_dict
        result = scan_social_context(body.url, task_id, body.caption)
        _scan_tasks[task_id] = {
            "status": "completed",
            "result": context_scan_to_dict(result),
        }

    return ScanURLResponse(task_id=task_id, status="scanning")


@router.get("/scan-result/{task_id}", response_model=ScanResultResponse)
def get_scan_result(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Poll for social context scan result.
    Returns status and result when complete.
    """
    task_data = _scan_tasks.get(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # Check Celery task status if still scanning
    if task_data["status"] == "scanning" and "celery_task_id" in task_data:
        try:
            from app.worker import celery_app
            celery_result = celery_app.AsyncResult(task_data["celery_task_id"])
            if celery_result.ready():
                task_data["status"] = "completed"
                task_data["result"] = celery_result.result
            elif celery_result.failed():
                task_data["status"] = "failed"
                task_data["result"] = {"error": str(celery_result.result)}
        except Exception:
            pass

    return ScanResultResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
    )


@router.post("/reverse-search", response_model=ReverseSearchResponse)
async def standalone_reverse_search(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Quick standalone reverse image search (no full pipeline).
    Accepts multipart image file.
    Use case: browser extension quick check.
    """
    tmp_path = f"/tmp/reverse_search_{uuid.uuid4()}_{file.filename}"
    try:
        contents = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(contents)

        from app.social.reverse_image_search import reverse_image_search, reverse_search_to_dict
        result = reverse_image_search(image_path=tmp_path)

        return ReverseSearchResponse(
            similar_images_found=result.similar_images_found,
            top_matches=result.top_matches,
            recontextualized_flag=result.recontextualized_flag,
            old_image_reposted_flag=result.old_image_reposted_flag,
            original_source_urls=result.original_source_urls,
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
