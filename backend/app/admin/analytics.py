import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# All analytics functions are called by Celery beat tasks.
# Results stored in Redis with appropriate TTLs.
# Admin dashboard frontend reads from these cached values only.
# Never compute analytics on-demand per admin request — always serve from cache.
# ─────────────────────────────────────────────────────────────────────────────

# [MOCK] Redis client placeholder
# from app.core.redis_client import redis_client


def compute_platform_stats():
    """
    Called every 5 minutes by Celery beat.
    Stored in Redis key "admin:platform_stats" TTL=300s.
    """
    now = datetime.utcnow()
    stats = {
        "total_analyses_all_time": 48_320,
        "analyses_last_24h": 412,
        "analyses_last_7d": 2_847,
        "active_users_last_24h": 189,          # users with at least 1 analysis in 24h
        "new_registrations_last_24h": 34,
        "high_risk_detections_last_24h": 67,
        "medium_risk_detections_last_24h": 112,
        "authentic_last_24h": 233,
        "avg_authenticity_score_last_24h": 72.4,
        "avg_processing_time_ms_last_24h": 3420.0,
        "total_posts_published": 8_740,
        "total_reports_filed": 312,
        "active_bans": 7,
        "agent_last_run": now.isoformat(),
        "lora_adapters_active": 3,
    }

    # [MOCK] In production:
    # stats["total_analyses_all_time"] = db.execute(
    #     select(func.count()).select_from(AnalysisJob)
    # ).scalar()
    # stats["analyses_last_24h"] = db.execute(
    #     select(func.count()).select_from(AnalysisJob)
    #     .where(AnalysisJob.created_at >= now - timedelta(hours=24))
    # ).scalar()
    # ... (full queries for each metric)

    # redis_client.setex("admin:platform_stats", 300, json.dumps(stats))
    logger.info("Computed platform stats")
    return stats


def compute_risk_distribution():
    """
    Called every 30 minutes by Celery beat.
    Returns counts of high/medium/authentic per media_type for last 30 days.
    Stored as "admin:risk_distribution" TTL=1800s.
    Used by donut chart on admin dashboard.
    """
    distribution = {
        "video": {"high": 120, "medium": 340, "authentic": 890},
        "image": {"high": 95, "medium": 210, "authentic": 1_420},
        "audio": {"high": 45, "medium": 88, "authentic": 520},
        "text":  {"high": 30, "medium": 74, "authentic": 610},
    }

    # [MOCK] In production:
    # query = (
    #     select(
    #         AnalysisResult.media_type,
    #         AnalysisResult.risk_level,
    #         func.count()
    #     )
    #     .where(AnalysisResult.created_at >= datetime.utcnow() - timedelta(days=30))
    #     .group_by(AnalysisResult.media_type, AnalysisResult.risk_level)
    # )

    # redis_client.setex("admin:risk_distribution", 1800, json.dumps(distribution))
    logger.info("Computed risk distribution")
    return distribution


def compute_technique_breakdown():
    """
    Called every hour by Celery beat.
    Aggregates flags_raised JSONB column across all analysis_results.
    Counts occurrences of each flag type.
    Stored as "admin:technique_breakdown" TTL=3600s.
    """
    breakdown = {
        "face_swap": 312,
        "neural_tts": 187,
        "lipsync_mismatch": 245,
        "gan_artifact": 156,
        "diffusion_artifact": 98,
        "metadata_tampering": 73,
        "copy_move": 42,
        "splicing": 61,
    }

    # [MOCK] In production:
    # Raw query to unnest JSONB array and count each flag:
    # SELECT flag, COUNT(*) FROM analysis_results,
    #   jsonb_array_elements_text(flags_raised) AS flag
    # GROUP BY flag ORDER BY count DESC

    # redis_client.setex("admin:technique_breakdown", 3600, json.dumps(breakdown))
    logger.info("Computed technique breakdown")
    return breakdown


def compute_daily_volume_timeseries():
    """
    Called every hour by Celery beat.
    Returns analysis count per day for last 30 days.
    Stored as "admin:daily_volume" TTL=3600s.
    """
    now = datetime.utcnow()
    timeseries = []
    for i in range(30):
        day = now - timedelta(days=i)
        timeseries.append({
            "date": day.strftime("%Y-%m-%d"),
            "count": 120 + (i * 3) % 50,  # mock data
        })

    # [MOCK] In production:
    # SELECT DATE(created_at), COUNT(*)
    # FROM analysis_jobs
    # GROUP BY DATE(created_at)
    # ORDER BY DATE(created_at) DESC LIMIT 30

    # redis_client.setex("admin:daily_volume", 3600, json.dumps(timeseries))
    logger.info("Computed daily volume timeseries")
    return timeseries


def compute_top_flagged_figures():
    """
    Called every 6 hours by Celery beat.
    Extract named entities from analysis fact_check_results JSONB.
    Count entity mention frequency across all high-risk analyses.
    Return top 20 most-targeted public figures with risk score distribution.
    Stored as "admin:top_flagged_figures" TTL=21600s.
    """
    figures = [
        {"name": "Public Figure A", "mention_count": 42, "avg_risk_score": 78.3},
        {"name": "Public Figure B", "mention_count": 38, "avg_risk_score": 65.1},
        {"name": "Public Figure C", "mention_count": 31, "avg_risk_score": 82.7},
    ]

    # [MOCK] In production:
    # Complex NER extraction + aggregation across fact_check_results JSONB

    # redis_client.setex("admin:top_flagged_figures", 21600, json.dumps(figures))
    logger.info("Computed top flagged figures")
    return figures


def compute_geographic_heatmap():
    """
    Called every 6 hours by Celery beat.
    For analyses where EXIF GPS metadata exists:
      Group by country code, count high-risk analyses per country.
    Stored as "admin:geo_heatmap" TTL=21600s.
    """
    heatmap = [
        {"country_code": "US", "count": 1_240, "risk_distribution": {"high": 180, "medium": 340, "authentic": 720}},
        {"country_code": "IN", "count": 890, "risk_distribution": {"high": 120, "medium": 280, "authentic": 490}},
        {"country_code": "GB", "count": 560, "risk_distribution": {"high": 78, "medium": 160, "authentic": 322}},
        {"country_code": "BR", "count": 430, "risk_distribution": {"high": 67, "medium": 130, "authentic": 233}},
    ]

    # [MOCK] In production:
    # SELECT country_code, risk_level, COUNT(*)
    # FROM analysis_results
    # WHERE exif_metadata->'gps' IS NOT NULL
    # GROUP BY country_code, risk_level

    # redis_client.setex("admin:geo_heatmap", 21600, json.dumps(heatmap))
    logger.info("Computed geographic heatmap")
    return heatmap
