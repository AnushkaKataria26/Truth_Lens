import asyncio
import json
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.auth.jwt_handler import get_current_user
from app.stream.stream_manager import (
    create_session,
    stop_session,
    get_user_sessions,
    get_session,
    update_session_task_id,
)
from app.stream.rtmp_ingestor import validate_stream_url
from app.stream.frame_sampler import get_segment_results, get_timeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/stream", tags=["stream"])


# ─── Request / Response Models ────────────────────────────────────────────────

class StreamStartRequest(BaseModel):
    stream_url: str
    stream_type: str = "hls"
    sample_interval_seconds: int = 2


class StreamStartResponse(BaseModel):
    session_id: str
    status: str


class StreamStopResponse(BaseModel):
    session_id: str
    total_segments_analyzed: int
    status: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StreamStartResponse)
def start_stream(
    body: StreamStartRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Start a new stream monitoring session.
    Validates URL reachability, creates session, and dispatches Celery task.
    """
    user_id = current_user["sub"]

    # Validate stream URL reachability (HEAD request, timeout=5s)
    if not validate_stream_url(body.stream_url):
        raise HTTPException(status_code=400, detail="Stream URL is not reachable")

    # Create session
    try:
        session = create_session(
            user_id=user_id,
            stream_url=body.stream_url,
            stream_type=body.stream_type,
            sample_interval_seconds=body.sample_interval_seconds,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Dispatch Celery task for continuous monitoring
    try:
        from app.worker import monitor_stream_task
        task = monitor_stream_task.delay(session.id)
        update_session_task_id(session.id, str(task.id))
    except Exception as e:
        logger.warning(f"Celery not available for stream task: {e}")

    return StreamStartResponse(session_id=session.id, status="active")


@router.post("/stop/{session_id}", response_model=StreamStopResponse)
def stop_stream(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Stop a stream session. Only the session owner can stop it."""
    user_id = current_user["sub"]

    try:
        session = stop_session(session_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not session owner")

    return StreamStopResponse(
        session_id=session.id,
        total_segments_analyzed=session.total_segments_analyzed,
        status="stopped",
    )


@router.get("/sessions")
def list_sessions(current_user: dict = Depends(get_current_user)):
    """Returns all active stream sessions for the current user."""
    return get_user_sessions(current_user["sub"])


@router.get("/results/{session_id}")
def session_results(
    session_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    risk_filter: Optional[str] = Query(None, regex="^(high|medium|authentic)$"),
    current_user: dict = Depends(get_current_user),
):
    """Paginated list of StreamSegmentResult for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not session owner")

    return get_segment_results(session_id, page, limit, risk_filter)


@router.get("/timeline/{session_id}")
def session_timeline(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    """
    Last N segment results for timeline visualization.
    Each point maps to: green (authentic), orange (medium), red (high).
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not session owner")

    return get_timeline(session_id, limit)


@router.get("/alerts/{session_id}")
async def stream_alerts(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Server-Sent Events (SSE) endpoint for real-time high-risk alerts.
    Frontend subscribes and receives JSON events per high-risk segment detection.
    Uses Redis pub/sub channel: "stream:{session_id}:alerts"
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not session owner")

    async def event_generator():
        # [MOCK] In production, use aioredis pub/sub:
        # import aioredis
        # redis = aioredis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))
        # pubsub = redis.pubsub()
        # await pubsub.subscribe(f"stream:{session_id}:alerts")
        # async for message in pubsub.listen():
        #     if message["type"] == "message":
        #         yield f"data: {message['data'].decode()}\n\n"

        # Mock: send a heartbeat every 5s to keep connection alive
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )
