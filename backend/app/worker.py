import os
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

celery_app = Celery(
    "truthlens",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        # LoRA fine-tuning runs on GPU-capable workers only
        "app.tasks.lora_fine_tune_task": {"queue": "gpu_queue"},
        # Stream analysis runs on a dedicated queue with concurrency=2
        # Start worker: celery -A app.tasks worker -Q stream_queue --concurrency=2
        # A single stream session should NOT consume all worker slots.
        "app.tasks.monitor_stream_task": {"queue": "stream_queue"},
    },
)

celery_app.conf.beat_schedule = {
    # RAG source refresh — every hour
    "refresh-rag-sources": {
        "task": "app.tasks.rag_refresh_task",
        "schedule": crontab(minute=0),  # every hour
    },
    # LangGraph agent continuous learning loop — daily at 2am UTC
    "run-agent-loop": {
        "task": "app.tasks.agent_task",
        "schedule": crontab(hour=2, minute=0),  # daily at 2am
    },
    # Insights trend computation — every 6 hours
    "compute-insights-trends": {
        "task": "app.tasks.compute_trends_task",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
    },
    # Leaderboard cache warm — every 5 minutes
    "compute-leaderboard-cache": {
        "task": "app.tasks.refresh_leaderboard_task",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
    # ─── Phase 4: Admin Analytics ──────────────────────────────────────
    "compute-platform-stats": {
        "task": "app.tasks.compute_platform_stats_task",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
    "compute-risk-distribution": {
        "task": "app.tasks.compute_risk_distribution_task",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
    },
    "compute-technique-breakdown": {
        "task": "app.tasks.compute_technique_breakdown_task",
        "schedule": crontab(minute=0),  # every hour
    },
    "compute-daily-volume": {
        "task": "app.tasks.compute_daily_volume_task",
        "schedule": crontab(minute=0),  # every hour
    },
    "compute-geo-heatmap": {
        "task": "app.tasks.compute_geo_heatmap_task",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
    },
    "generate-daily-report": {
        "task": "app.tasks.generate_daily_report_task",
        "schedule": crontab(hour=6, minute=0),  # daily at 6am UTC
    },
    "generate-weekly-report": {
        "task": "app.tasks.generate_weekly_report_task",
        "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Monday 06:00 UTC
    },
}

# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@celery_app.task(name="app.tasks.rag_refresh_task")
def rag_refresh_task():
    from app.rag.source_manager import refresh_stale_sources
    refresh_stale_sources()


@celery_app.task(name="app.tasks.agent_task", bind=True, max_retries=0)
def agent_task(self):
    """
    The LangGraph agent must be idempotent.
    Uses a Redis distributed lock to prevent concurrent runs.
    """
    import redis
    r = redis.Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

    # Acquire lock: SET "agent:lock" 1 NX EX 3600
    lock_acquired = r.set("agent:lock", "1", nx=True, ex=3600)
    if not lock_acquired:
        print("[AGENT] Another agent run is already in progress. Skipping.")
        return "skipped — lock held"

    try:
        from app.agents.agent_graph import agent
        result = agent.invoke({"trigger": "scheduled"})
        return result.get("summary_report", "done")
    finally:
        r.delete("agent:lock")


@celery_app.task(name="app.tasks.lora_fine_tune_task", queue="gpu_queue")
def lora_fine_tune_task(attack_type: str):
    """Runs on the gpu_queue — separate from default CPU workers."""
    from app.agents.tools.lora_updater import run_fine_tune_task
    run_fine_tune_task(attack_type)


@celery_app.task(name="app.tasks.compute_trends_task")
def compute_trends_task():
    from app.api.routes.insights import compute_trends
    compute_trends()


@celery_app.task(name="app.tasks.refresh_leaderboard_task")
def refresh_leaderboard_task():
    # [MOCK] Recompute leaderboard rankings and cache in Redis
    pass


# ─── Phase 4: Admin Analytics Tasks ───────────────────────────────────────────

@celery_app.task(name="app.tasks.compute_platform_stats_task")
def compute_platform_stats_task():
    from app.admin.analytics import compute_platform_stats
    compute_platform_stats()


@celery_app.task(name="app.tasks.compute_risk_distribution_task")
def compute_risk_distribution_task():
    from app.admin.analytics import compute_risk_distribution
    compute_risk_distribution()


@celery_app.task(name="app.tasks.compute_technique_breakdown_task")
def compute_technique_breakdown_task():
    from app.admin.analytics import compute_technique_breakdown
    compute_technique_breakdown()


@celery_app.task(name="app.tasks.compute_daily_volume_task")
def compute_daily_volume_task():
    from app.admin.analytics import compute_daily_volume_timeseries
    compute_daily_volume_timeseries()


@celery_app.task(name="app.tasks.compute_geo_heatmap_task")
def compute_geo_heatmap_task():
    from app.admin.analytics import compute_top_flagged_figures, compute_geographic_heatmap
    compute_top_flagged_figures()
    compute_geographic_heatmap()


@celery_app.task(name="app.tasks.generate_daily_report_task")
def generate_daily_report_task():
    from app.admin.reporting import generate_daily_report
    generate_daily_report()


@celery_app.task(name="app.tasks.generate_weekly_report_task")
def generate_weekly_report_task():
    from app.admin.reporting import generate_weekly_report
    generate_weekly_report()


# ─── Phase 4: Stream Monitoring Task ─────────────────────────────────────────

@celery_app.task(name="app.tasks.monitor_stream_task", bind=True)
def monitor_stream_task(self, session_id: str):
    """
    Long-running Celery task for continuous stream monitoring.
    Starts FFmpeg capture, polls for new frames, and analyzes each segment.
    Runs until the session is stopped (task revoked).
    """
    import time

    from app.stream.stream_manager import get_session
    from app.stream.rtmp_ingestor import start_stream_capture, start_audio_capture
    from app.stream.frame_sampler import FrameWatcher
    from app.stream.stream_analyzer import analyze_segment

    session = get_session(session_id)
    if not session:
        return "session_not_found"

    output_dir = f"/tmp/stream_{session_id}"
    sample_interval = session.sample_interval_seconds

    # Start FFmpeg capture processes
    start_stream_capture(session.stream_url, session_id, output_dir, sample_interval)
    start_audio_capture(session.stream_url, session_id, output_dir, sample_interval)

    # Create frame watcher
    watcher = FrameWatcher(session_id, output_dir, sample_interval)

    # Continuous monitoring loop — runs until task is revoked
    try:
        while True:
            new_frames = watcher.poll_new_frames()

            for frame_path in new_frames:
                if not watcher.is_file_complete(frame_path):
                    continue

                seg_idx = watcher.next_segment_index()
                frame_ts = seg_idx * sample_interval

                # Check for corresponding audio segment
                audio_path = os.path.join(
                    output_dir, "audio", f"audio_{seg_idx:08d}.wav"
                )
                audio = audio_path if os.path.exists(audio_path) else None

                # Run analysis
                analyze_segment(
                    session_id=session_id,
                    segment_index=seg_idx,
                    frame_path=frame_path,
                    audio_path=audio,
                    frame_timestamp=frame_ts,
                )

                watcher.mark_processed(frame_path)

            # Cleanup old frames (60s rolling window)
            watcher.cleanup_old_frames(max_age_seconds=60)

            # Poll interval: slightly less than sample interval
            time.sleep(max(0.5, sample_interval - 0.5))

    except Exception as e:
        logger.error(f"Stream monitor error for {session_id}: {e}")
        return f"error: {e}"


# ─── Phase 4: Social Context Scan Task ────────────────────────────────────────

@celery_app.task(name="app.tasks.social_scan_task")
def social_scan_task(post_url: str, job_id: str, caption: str = None):
    """
    Async social context scan via Celery.
    Runs: yt-dlp download → reverse image search → velocity tracking → GPS check.
    """
    from app.social.context_scanner import scan_social_context, context_scan_to_dict
    result = scan_social_context(post_url, job_id, caption)
    return context_scan_to_dict(result)
