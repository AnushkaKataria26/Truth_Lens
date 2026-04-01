import uuid
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# DB Model reference (actual model goes in db_models.py)
# ─────────────────────────────────────────────────────────────────────────────
# class StreamSession(Base):
#     __tablename__ = "stream_sessions"
#     id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
#     stream_url = Column(String, nullable=False)
#     stream_type = Column(String, nullable=False)  # "rtmp"|"hls"|"youtube_live"|"custom_hls"
#     status = Column(String, default="active")     # "active"|"paused"|"stopped"|"error"
#     sample_interval_seconds = Column(Integer, default=2)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     last_frame_at = Column(DateTime, nullable=True)
#     total_segments_analyzed = Column(Integer, default=0)
#     celery_task_id = Column(String, nullable=True)

VALID_STREAM_TYPES = {"rtmp", "hls", "youtube_live", "custom_hls"}
VALID_STATUSES = {"active", "paused", "stopped", "error"}


@dataclass
class StreamSessionData:
    id: str
    user_id: str
    stream_url: str
    stream_type: str
    status: str = "active"
    sample_interval_seconds: int = 2
    created_at: str = ""
    last_frame_at: Optional[str] = None
    total_segments_analyzed: int = 0
    celery_task_id: Optional[str] = None


# In-memory store for mock
_sessions: dict[str, StreamSessionData] = {}


def create_session(
    user_id: str,
    stream_url: str,
    stream_type: str,
    sample_interval_seconds: int = 2,
) -> StreamSessionData:
    """Create a new stream session record."""
    if stream_type not in VALID_STREAM_TYPES:
        raise ValueError(f"Invalid stream_type: {stream_type}")
    if not 1 <= sample_interval_seconds <= 10:
        raise ValueError("sample_interval_seconds must be 1-10")

    session = StreamSessionData(
        id=str(uuid.uuid4()),
        user_id=user_id,
        stream_url=stream_url,
        stream_type=stream_type,
        sample_interval_seconds=sample_interval_seconds,
        created_at=datetime.utcnow().isoformat(),
    )

    # [MOCK] In production: db.add(StreamSession(...)); db.commit()
    _sessions[session.id] = session
    logger.info(f"Created stream session {session.id} for user {user_id}")
    return session


def stop_session(session_id: str, user_id: str) -> StreamSessionData:
    """
    Stop a stream session. Revokes Celery task, updates status.
    Only the session owner can stop it.
    """
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found")
    if session.user_id != user_id:
        raise PermissionError("Not session owner")

    # Revoke Celery task
    if session.celery_task_id:
        try:
            from app.worker import celery_app
            celery_app.control.revoke(session.celery_task_id, terminate=True)
        except Exception as e:
            logger.warning(f"Failed to revoke Celery task: {e}")

    # Stop FFmpeg capture
    from app.stream.rtmp_ingestor import stop_stream_capture
    stop_stream_capture(session_id)

    session.status = "stopped"
    logger.info(f"Stopped stream session {session_id} (segments={session.total_segments_analyzed})")
    return session


def get_user_sessions(user_id: str) -> list[dict]:
    """Returns all active sessions for the given user."""
    # [MOCK] In production: db.query(StreamSession).filter_by(user_id=user_id, status="active")
    return [
        asdict(s) for s in _sessions.values()
        if s.user_id == user_id and s.status == "active"
    ]


def get_session(session_id: str) -> Optional[StreamSessionData]:
    """Fetch a single session by ID."""
    return _sessions.get(session_id)


def update_session_task_id(session_id: str, task_id: str):
    """Store the Celery task ID on the session for later revocation."""
    session = _sessions.get(session_id)
    if session:
        session.celery_task_id = task_id


def increment_segment_count(session_id: str):
    """Called after each segment is analyzed."""
    session = _sessions.get(session_id)
    if session:
        session.total_segments_analyzed += 1
        session.last_frame_at = datetime.utcnow().isoformat()
