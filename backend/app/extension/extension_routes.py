import os
import uuid
import time
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.auth.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/extension", tags=["extension"])

# ─── Rate Limiting ────────────────────────────────────────────────────────────
# Uses slowapi for IP-based rate limiting on unauthenticated endpoints
# In production: Limiter is initialised in main.py and shared via app.state

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    RATE_LIMIT_AVAILABLE = False
    limiter = None
    logger.warning("slowapi not installed — rate limiting disabled for extension endpoints")


# ─── Model Preloading ────────────────────────────────────────────────────────
# Quick-scan models are loaded into the WEB WORKER process (not Celery worker).
# This avoids Celery task dispatch overhead — the 3s target is not achievable
# through Celery round-trip. Models are loaded at module import time so they
# persist in memory across requests.

_efficientnet_model = None
_clip_model = None
_models_loaded = False


def _preload_models():
    """
    Load EfficientNetV2 and CLIP into module-level variables.
    Called once at FastAPI startup via @app.on_event("startup").
    These run in the uvicorn web worker, NOT in a Celery worker.
    """
    global _efficientnet_model, _clip_model, _models_loaded

    if _models_loaded:
        return

    try:
        # [MOCK] In production:
        # import torch
        # from torchvision.models import efficientnet_v2_s
        # _efficientnet_model = efficientnet_v2_s(weights="DEFAULT")
        # _efficientnet_model.eval()
        # if torch.cuda.is_available():
        #     _efficientnet_model = _efficientnet_model.cuda()
        #
        # import clip
        # _clip_model, _clip_preprocess = clip.load("ViT-B/32", device="cuda" if torch.cuda.is_available() else "cpu")

        _efficientnet_model = "efficientnet_v2_mock"
        _clip_model = "clip_vit_b32_mock"
        _models_loaded = True
        logger.info("Quick-scan models preloaded: EfficientNetV2 + CLIP (in web worker)")
    except Exception as e:
        logger.error(f"Failed to preload quick-scan models: {e}")


# ─── In-memory stores (mock) ─────────────────────────────────────────────────

_quick_scans: dict[str, dict] = {}       # scan_id → quick scan result
_extension_reports: list[dict] = []      # user reports for admin review


# ─── Request / Response Models ────────────────────────────────────────────────

class QuickScanURLRequest(BaseModel):
    image_url: str


class QuickScanResponse(BaseModel):
    quick_score: float            # 0–100
    risk_level: str               # "high" | "medium" | "authentic"
    flags: list
    reverse_search_match: bool
    scan_id: str                  # UUID — can upgrade to full analysis


class FullAnalysisRequest(BaseModel):
    scan_id: Optional[str] = None     # upgrade quick-scan
    url: Optional[str] = None         # fresh full analysis from URL


class FullAnalysisResponse(BaseModel):
    job_id: str
    status: str


class ExtensionReportRequest(BaseModel):
    url: str
    reason: str
    media_type: str = "image"


class ExtensionReportResponse(BaseModel):
    report_id: str
    status: str


# ─── Quick Scan (no auth, rate-limited by IP) ─────────────────────────────────

def _run_quick_scan(image_path: str) -> dict:
    """
    Lightweight pipeline for < 3s response:
      1. EfficientNetV2 face check (~150ms)
      2. CLIP image-text anomaly (~100ms)
      3. Reverse image search — async, cached
    Skip: audio, RAG fact-check, LipSync, LoRA, full provenance
    """
    start = time.time()

    # [MOCK] Step 1: Face detection + deepfake classification
    fake_probability = 0.25  # mock
    flags = []
    if fake_probability > 0.6:
        flags.append("face_swap_detected")
    if fake_probability > 0.8:
        flags.append("high_confidence_fake")

    # [MOCK] Step 2: CLIP image-text anomaly
    clip_anomaly = 0.10  # mock
    if clip_anomaly > 0.5:
        flags.append("clip_anomaly")

    # [MOCK] Step 3: Reverse search (top result only for speed)
    reverse_match = False  # mock

    # Compute quick score (0–100)
    quick_score = round((1.0 - fake_probability) * 70 + (1.0 - clip_anomaly) * 30, 1)

    if quick_score < 40:
        risk_level = "high"
    elif quick_score < 70:
        risk_level = "medium"
    else:
        risk_level = "authentic"

    processing_ms = int((time.time() - start) * 1000)
    logger.info(f"Quick scan: score={quick_score} risk={risk_level} time={processing_ms}ms")

    return {
        "quick_score": quick_score,
        "risk_level": risk_level,
        "flags": flags,
        "reverse_search_match": reverse_match,
    }


@router.post("/quick-scan", response_model=QuickScanResponse)
async def quick_scan(
    request: Request,
    body: Optional[QuickScanURLRequest] = None,
    file: Optional[UploadFile] = File(None),
):
    """
    Quick scan for browser extension — no auth required.
    Rate limit: 10 requests/minute per IP.
    Accepts image_url in body OR multipart file upload.
    Target latency: < 3 seconds on GPU.
    """
    # Apply rate limit manually if slowapi is available
    # (In production, use @limiter.limit("10/minute") decorator with app.state.limiter)

    scan_id = str(uuid.uuid4())
    tmp_path = None

    try:
        if file and file.filename:
            # File upload path
            tmp_path = f"/tmp/extension_scan_{scan_id}"
            contents = await file.read()
            with open(tmp_path, "wb") as f:
                f.write(contents)
        elif body and body.image_url:
            # URL download path
            tmp_path = f"/tmp/extension_scan_{scan_id}"
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(body.image_url)
                    resp.raise_for_status()
                    with open(tmp_path, "wb") as f:
                        f.write(resp.content)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Cannot fetch image: {e}")
        else:
            raise HTTPException(status_code=400, detail="Provide image_url or file upload")

        # Run lightweight pipeline
        result = _run_quick_scan(tmp_path)
        result["scan_id"] = scan_id

        # Cache scan result for potential full-analysis upgrade
        _quick_scans[scan_id] = {
            "image_path": tmp_path,
            "result": result,
            "created_at": time.time(),
        }

        return QuickScanResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick scan error: {e}")
        raise HTTPException(status_code=500, detail="Scan failed")


# ─── Full Analysis (auth required) ────────────────────────────────────────────

@router.post("/full-analysis", response_model=FullAnalysisResponse)
def full_analysis(
    body: FullAnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Upgrade a quick-scan to full pipeline, or start fresh from URL.
    Auth required — extension must be signed in.
    Dispatches standard Celery analysis_task.
    """
    job_id = str(uuid.uuid4())

    if body.scan_id:
        # Upgrade quick-scan
        scan_data = _quick_scans.get(body.scan_id)
        if not scan_data:
            raise HTTPException(status_code=404, detail="Quick scan not found or expired")

        # [MOCK] In production: dispatch analysis_task with the cached file
        # from app.worker import analysis_task
        # task = analysis_task.delay(job_id, scan_data["image_path"])
        logger.info(f"Upgraded quick-scan {body.scan_id} to full analysis {job_id}")

    elif body.url:
        # Fresh full analysis from URL
        # [MOCK] In production:
        # from app.worker import analysis_task
        # task = analysis_task.delay(job_id, url=body.url)
        logger.info(f"Full analysis from URL: {body.url} → job {job_id}")

    else:
        raise HTTPException(status_code=400, detail="Provide scan_id or url")

    return FullAnalysisResponse(job_id=job_id, status="queued")


# ─── Status (reuse existing analyze endpoint) ─────────────────────────────────
# GET /api/v1/extension/status/{job_id}
# This is just a proxy to the existing analyze status endpoint for convenience.

@router.get("/status/{job_id}")
def extension_status(job_id: str):
    """
    Get analysis status — same as /api/v1/analyze/status/{job_id}.
    Extension polls this for full analysis progress.
    """
    # [MOCK] In production: reuse results endpoint
    # from app.api.routes.results import get_job_status
    # return get_job_status(job_id)
    return {
        "job_id": job_id,
        "status": "completed",  # mock
        "progress": 100,
    }


# ─── User Report ──────────────────────────────────────────────────────────────

@router.post("/report", response_model=ExtensionReportResponse)
def extension_report(
    body: ExtensionReportRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a user report from the browser extension.
    Creates a report without running full analysis.
    Stored in DB for admin review.
    Increments report_count if URL matches existing analyzed post.
    """
    report_id = str(uuid.uuid4())

    report = {
        "id": report_id,
        "user_id": current_user["sub"],
        "url": body.url,
        "reason": body.reason,
        "media_type": body.media_type,
        "status": "pending_review",
        "created_at": time.time(),
    }

    # [MOCK] In production:
    # db.add(ExtensionReport(
    #     user_id=current_user["sub"],
    #     url=body.url,
    #     reason=body.reason,
    #     media_type=body.media_type,
    # ))
    # db.commit()
    # Increment report count on matching post:
    # db.query(Post).filter_by(url=body.url).update({Post.report_count: Post.report_count + 1})

    _extension_reports.append(report)
    logger.info(f"Extension report submitted: {report_id} url={body.url}")

    return ExtensionReportResponse(report_id=report_id, status="pending_review")
