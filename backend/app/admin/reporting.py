import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# [MOCK] In production:
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")
# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# In-memory store for mock
_reports_store: list[dict] = []


def _send_report_email(subject: str, report: dict):
    """
    Send report via SendGrid or SMTP to all admin email addresses.
    """
    admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    admin_emails = [e.strip() for e in admin_emails if e.strip()]

    if not admin_emails:
        logger.info("No admin emails configured — skipping email delivery")
        return

    # [MOCK] In production:
    # message = Mail(
    #     from_email="noreply@truthlens.ai",
    #     to_emails=admin_emails,
    #     subject=subject,
    #     html_content=_render_report_html(report),
    # )
    # sg = SendGridAPIClient(SENDGRID_API_KEY)
    # sg.send(message)
    logger.info(f"[MOCK] Would email report '{subject}' to {admin_emails}")


def generate_weekly_report() -> dict:
    """
    Called every Monday 06:00 UTC by Celery beat.
    Generates a comprehensive weekly report covering:
      - Total analyses this week vs last week (% change)
      - New high-risk detections breakdown by technique
      - Trust Index leaderboard top 10 changes
      - Agent loop summary: papers processed, patterns extracted, fine-tunes triggered
      - Moderation actions taken: posts removed, accounts banned
      - System health: avg processing time, error rate, cache hit rate

    Stored as JSONB in DB table: weekly_reports.
    Also emailed to admin addresses in config.
    """
    now = datetime.utcnow()
    week_end = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    report = {
        "report_type": "weekly",
        "week_start": week_start,
        "week_end": week_end,
        "generated_at": now.isoformat(),

        # Analysis volume
        "analyses": {
            "this_week": 2_847,
            "last_week": 2_629,
            "change_pct": 8.3,
        },

        # Risk breakdown by technique
        "high_risk_by_technique": {
            "face_swap": 120,
            "neural_tts": 87,
            "lipsync_mismatch": 65,
            "gan_artifact": 42,
            "diffusion_artifact": 31,
            "metadata_tampering": 18,
            "splicing": 12,
        },

        # Trust leaderboard changes (top 10)
        "trust_leaderboard_top10": [
            {"username": "factchecker_pro", "trust_index": 92.3, "change": +4.1},
            {"username": "media_analyst", "trust_index": 88.7, "change": +2.8},
            {"username": "deepfake_hunter", "trust_index": 85.1, "change": +6.2},
            {"username": "truth_seeker_42", "trust_index": 81.4, "change": -1.3},
            {"username": "verify_first", "trust_index": 79.8, "change": +3.5},
        ],

        # Agent loop summary
        "agent_summary": {
            "cycles_completed": 7,
            "arxiv_papers_processed": 42,
            "hf_models_scanned": 18,
            "novel_patterns_extracted": 12,
            "lora_fine_tunes_triggered": 2,
            "rag_documents_indexed": 156,
        },

        # Moderation actions
        "moderation": {
            "posts_removed": 8,
            "accounts_banned": 2,
            "accounts_unbanned": 1,
            "risk_overrides": 5,
            "reports_resolved": 34,
        },

        # System health
        "system_health": {
            "avg_processing_time_ms": 3420,
            "p95_processing_time_ms": 8100,
            "error_rate_pct": 0.4,
            "cache_hit_rate_pct": 94.2,
            "gpu_utilization_avg_pct": 67.3,
        },
    }

    # [MOCK] In production:
    # db.add(WeeklyReport(
    #     week_start=week_start, week_end=week_end,
    #     data=report, generated_at=now,
    # ))
    # db.commit()
    # redis_client.setex(f"admin:weekly_report:{week_start}", 2592000, json.dumps(report))

    _reports_store.append(report)

    # Email to admins
    _send_report_email(
        subject=f"TruthLens Weekly Report: {week_start} – {week_end}",
        report=report,
    )

    logger.info(f"Generated weekly report for {week_start} to {week_end}")
    return report


def generate_daily_report() -> dict:
    """
    Called daily at 6am UTC by Celery beat.
    Lighter-weight daily summary.
    Stored in Redis "admin:daily_report:{date}" TTL=604800 (7 days).
    Also persisted to DB table: admin_reports.
    """
    yesterday = datetime.utcnow().strftime("%Y-%m-%d")

    report = {
        "report_type": "daily",
        "report_date": yesterday,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_analyses": 412,
            "high_risk": 67,
            "medium_risk": 112,
            "authentic": 233,
            "new_users": 34,
            "posts_published": 89,
            "reports_filed": 12,
        },
        "notable_events": [
            "3 new LoRA adapters deployed for face_swap detection",
            "Agent cycle completed: 12 new papers indexed, 4 novel patterns extracted",
            "High-velocity trend detected: political deepfake claim on Twitter (850+ shares in 4h)",
        ],
        "top_flagged_content": [
            {"job_id": "mock-uuid-1", "risk_level": "high", "authenticity_score": 12.5},
            {"job_id": "mock-uuid-2", "risk_level": "high", "authenticity_score": 18.3},
        ],
        "agent_summary": "Fetched 12 arXiv papers, extracted 4 novel patterns, triggered 1 LoRA fine-tune.",
    }

    # [MOCK] In production:
    # redis_client.setex(f"admin:daily_report:{yesterday}", 604800, json.dumps(report))
    # db.add(AdminReport(date=yesterday, report_type="daily", data=report)); db.commit()

    _reports_store.append(report)

    logger.info(f"Generated daily report for {yesterday}")
    return report


def get_reports(report_type: str = "weekly", limit: int = 12) -> list[dict]:
    """
    Returns the last N reports of the given type, newest first.
    GET /api/v1/admin/reports?type=weekly&limit=12
    """
    # [MOCK] In production:
    # return db.query(WeeklyReport).order_by(WeeklyReport.generated_at.desc()).limit(limit).all()

    filtered = [r for r in reversed(_reports_store) if r.get("report_type") == report_type]
    return filtered[:limit]
