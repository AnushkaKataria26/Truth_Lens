import os
import time
import glob
import logging
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# DB Model reference (actual model goes in db_models.py)
# ─────────────────────────────────────────────────────────────────────────────
# class StreamSegmentResult(Base):
#     __tablename__ = "stream_segment_results"
#     id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     session_id = Column(UUID, ForeignKey("stream_sessions.id"), nullable=False)
#     segment_index = Column(Integer, nullable=False)
#     frame_timestamp = Column(Float, nullable=False)     # seconds from stream start
#     authenticity_score = Column(Float, nullable=False)
#     risk_level = Column(String, nullable=False)
#     flags_raised = Column(JSONB, default=[])
#     heatmap_s3_url = Column(String, nullable=True)
#     processing_time_ms = Column(Integer, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)


@dataclass
class SegmentResult:
    id: str
    session_id: str
    segment_index: int
    frame_timestamp: float
    authenticity_score: float
    risk_level: str
    flags_raised: list
    heatmap_s3_url: Optional[str]
    processing_time_ms: int
    created_at: str


# In-memory store for mock
_segment_results: dict[str, list[SegmentResult]] = {}


def store_segment_result(result: SegmentResult):
    """Persist a segment result to DB and in-memory cache."""
    # [MOCK] In production: db.add(StreamSegmentResult(...)); db.commit()
    if result.session_id not in _segment_results:
        _segment_results[result.session_id] = []
    _segment_results[result.session_id].append(result)


def get_segment_results(
    session_id: str,
    page: int = 1,
    limit: int = 50,
    risk_filter: Optional[str] = None,
) -> dict:
    """Paginated segment results for a session."""
    results = _segment_results.get(session_id, [])
    if risk_filter:
        results = [r for r in results if r.risk_level == risk_filter]

    # newest first
    results = list(reversed(results))
    start = (page - 1) * limit
    page_results = results[start:start + limit]

    return {
        "items": [asdict(r) for r in page_results],
        "total": len(results),
        "page": page,
        "limit": limit,
    }


def get_timeline(session_id: str, limit: int = 100) -> list[dict]:
    """
    Returns last N segment results for timeline visualization.
    Each entry maps to a color-coded point: green (authentic), orange (medium), red (high).
    """
    results = _segment_results.get(session_id, [])
    recent = results[-limit:] if len(results) > limit else results
    return [
        {
            "segment_index": r.segment_index,
            "frame_timestamp": r.frame_timestamp,
            "authenticity_score": r.authenticity_score,
            "risk_level": r.risk_level,
            "flags_raised": r.flags_raised,
        }
        for r in recent
    ]


class FrameWatcher:
    """
    Watches output_dir for new frame files.
    When a new frame is detected and file write is complete (size stable):
      1. Read frame → pass to stream_analyzer
      2. Move processed frame to processed/ subdir
      3. Delete processed frames older than 60 seconds (rolling window)

    In production, uses watchdog library for filesystem events.
    Here we implement a polling-based approach for the Celery task.
    """

    def __init__(self, session_id: str, output_dir: str, sample_interval: int = 2):
        self.session_id = session_id
        self.output_dir = output_dir
        self.processed_dir = os.path.join(output_dir, "processed")
        self.sample_interval = sample_interval
        self.segment_index = 0
        self._processed_files: set[str] = set()

        os.makedirs(self.processed_dir, exist_ok=True)

    def poll_new_frames(self) -> list[str]:
        """Find new unprocessed frame files in the output directory."""
        frame_files = sorted(glob.glob(os.path.join(self.output_dir, "frame_*.jpg")))
        new_frames = [f for f in frame_files if f not in self._processed_files]
        return new_frames

    def is_file_complete(self, filepath: str, wait_ms: int = 200) -> bool:
        """Check if file write is complete by verifying size stability."""
        try:
            size1 = os.path.getsize(filepath)
            time.sleep(wait_ms / 1000)
            size2 = os.path.getsize(filepath)
            return size1 == size2 and size1 > 0
        except OSError:
            return False

    def mark_processed(self, filepath: str):
        """Move frame to processed/ subdirectory."""
        self._processed_files.add(filepath)
        try:
            dest = os.path.join(self.processed_dir, os.path.basename(filepath))
            os.rename(filepath, dest)
        except OSError as e:
            logger.warning(f"Failed to move processed frame: {e}")

    def cleanup_old_frames(self, max_age_seconds: int = 60):
        """Delete processed frames older than max_age_seconds (disk management)."""
        now = time.time()
        for f in glob.glob(os.path.join(self.processed_dir, "frame_*.jpg")):
            try:
                if now - os.path.getmtime(f) > max_age_seconds:
                    os.remove(f)
            except OSError:
                pass

    def next_segment_index(self) -> int:
        idx = self.segment_index
        self.segment_index += 1
        return idx
