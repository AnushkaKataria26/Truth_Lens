from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

from app.auth.jwt_handler import require_admin
from app.admin.analytics import (
    compute_platform_stats,
    compute_risk_distribution,
    compute_technique_breakdown,
    compute_daily_volume_timeseries,
    compute_top_flagged_figures,
    compute_geographic_heatmap,
)
from app.admin.audit_log import log_admin_action, get_audit_log
from app.admin.reporting import get_reports
from app.community.services.moderation import (
    remove_post,
    override_risk,
    ban_user,
    get_moderation_queue,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ─── Response Models ──────────────────────────────────────────────────────────

class PlatformStatsResponse(BaseModel):
    total_analyses_all_time: int
    analyses_last_24h: int
    analyses_last_7d: int
    active_users_last_24h: int
    new_registrations_last_24h: int
    high_risk_detections_last_24h: int
    medium_risk_detections_last_24h: int
    authentic_last_24h: int
    avg_authenticity_score_last_24h: float
    avg_processing_time_ms_last_24h: float
    total_posts_published: int
    total_reports_filed: int
    active_bans: int
    agent_last_run: str
    lora_adapters_active: int


class TechniqueEntry(BaseModel):
    flag_type: str
    count: int
    percentage: float


class DailyVolumeEntry(BaseModel):
    date: str
    count: int


class FlaggedFigureEntry(BaseModel):
    name: str
    mention_count: int
    avg_risk_score: float


class GeoHeatmapEntry(BaseModel):
    country_code: str
    count: int
    risk_distribution: dict


class ViralAlertEntry(BaseModel):
    post_id: str
    media_url: str
    risk_level: str
    velocity_score: float
    platform: str
    detected_at: str


class ModerationActionBody(BaseModel):
    reason: Optional[str] = None


class OverrideRiskBody(BaseModel):
    new_risk: str
    reason: Optional[str] = None


# ─── Analytics (all serve from Redis cache) ───────────────────────────────────

@router.get("/analytics/platform-stats", response_model=PlatformStatsResponse)
def platform_stats(admin: dict = Depends(require_admin)):
    """Reads 'admin:platform_stats' from Redis. Sub-10ms response."""
    # [MOCK] returning computed values; in production: redis_client.get("admin:platform_stats")
    return compute_platform_stats()


@router.get("/analytics/risk-distribution")
def risk_distribution(
    period: str = Query("30d", regex="^(7d|30d|90d)$", description="Time period: 7d, 30d, or 90d"),
    admin: dict = Depends(require_admin),
):
    """
    Reads 'admin:risk_distribution' from Redis.
    Query param `period` reserved for future multi-period support — currently serves 30d data.
    """
    # [MOCK] period param stored but not yet used in computation
    return compute_risk_distribution()


@router.get("/analytics/technique-breakdown", response_model=List[TechniqueEntry])
def technique_breakdown(admin: dict = Depends(require_admin)):
    """Reads 'admin:technique_breakdown' from Redis."""
    raw = compute_technique_breakdown()
    total = sum(raw.values()) or 1
    return [
        TechniqueEntry(
            flag_type=flag,
            count=count,
            percentage=round(count / total * 100, 1),
        )
        for flag, count in sorted(raw.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/analytics/daily-volume", response_model=List[DailyVolumeEntry])
def daily_volume(admin: dict = Depends(require_admin)):
    """Reads 'admin:daily_volume' from Redis — 30 entries."""
    return compute_daily_volume_timeseries()


@router.get("/analytics/top-figures", response_model=List[FlaggedFigureEntry])
def top_flagged_figures(admin: dict = Depends(require_admin)):
    """Reads 'admin:top_flagged_figures' from Redis."""
    return compute_top_flagged_figures()


@router.get("/analytics/geo-heatmap", response_model=List[GeoHeatmapEntry])
def geo_heatmap(admin: dict = Depends(require_admin)):
    """Reads 'admin:geo_heatmap' from Redis."""
    return compute_geographic_heatmap()


@router.get("/analytics/viral-alerts", response_model=List[ViralAlertEntry])
def viral_alerts(admin: dict = Depends(require_admin)):
    """
    Reads from Redis sorted set 'viral:alerts' — populated by velocity_tracker.
    Returns top 20 alerts ordered by velocity score descending.
    """
    # [MOCK] In production:
    # raw = redis_client.zrevrange("viral:alerts", 0, 19, withscores=True)
    # return [json.loads(item) for item, score in raw]
    return [
        ViralAlertEntry(
            post_id="mock-post-1",
            media_url="https://cdn.truthlens.ai/media/mock1.mp4",
            risk_level="high",
            velocity_score=2450.0,
            platform="twitter",
            detected_at="2026-03-26T10:00:00Z",
        ),
        ViralAlertEntry(
            post_id="mock-post-2",
            media_url="https://cdn.truthlens.ai/media/mock2.jpg",
            risk_level="high",
            velocity_score=1830.0,
            platform="reddit",
            detected_at="2026-03-26T09:15:00Z",
        ),
    ]


# ─── Moderation ───────────────────────────────────────────────────────────────

@router.get("/moderation/queue")
def moderation_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    admin: dict = Depends(require_admin),
):
    return get_moderation_queue(skip, limit)


@router.post("/moderation/posts/{post_id}/remove")
def admin_remove_post(
    post_id: str,
    body: ModerationActionBody,
    request: Request,
    admin: dict = Depends(require_admin),
):
    remove_post(post_id)
    log_admin_action(
        admin_user_id=admin["sub"],
        action_type="remove_post",
        target_type="post",
        target_id=post_id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/moderation/posts/{post_id}/override-risk")
def admin_override_risk(
    post_id: str,
    body: OverrideRiskBody,
    request: Request,
    admin: dict = Depends(require_admin),
):
    old_risk = "unknown"  # [MOCK] fetch current risk from DB
    override_risk(post_id, body.new_risk)
    log_admin_action(
        admin_user_id=admin["sub"],
        action_type="override_risk",
        target_type="post",
        target_id=post_id,
        reason=body.reason,
        metadata={"before": old_risk, "after": body.new_risk},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/moderation/users/{user_id}/ban")
def admin_ban_user(
    user_id: str,
    body: ModerationActionBody,
    request: Request,
    admin: dict = Depends(require_admin),
):
    ban_user(user_id)
    log_admin_action(
        admin_user_id=admin["sub"],
        action_type="ban_user",
        target_type="user",
        target_id=user_id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/moderation/users/{user_id}/unban")
def admin_unban_user(
    user_id: str,
    body: ModerationActionBody,
    request: Request,
    admin: dict = Depends(require_admin),
):
    # [MOCK] unban logic: UPDATE users SET is_banned=False WHERE id=user_id
    log_admin_action(
        admin_user_id=admin["sub"],
        action_type="unban_user",
        target_type="user",
        target_id=user_id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


# ─── Agent Control ────────────────────────────────────────────────────────────

@router.post("/agent/run")
def admin_trigger_agent(request: Request, admin: dict = Depends(require_admin)):
    """Manual agent trigger — dispatches to Celery."""
    try:
        from app.worker import agent_task
        task = agent_task.delay()
        log_admin_action(
            admin_user_id=admin["sub"],
            action_type="agent_manual_trigger",
            target_type="agent",
            target_id=str(task.id),
            ip_address=request.client.host if request.client else None,
        )
        return {"task_id": str(task.id), "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger agent: {e}")


# ─── Audit Log ────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def admin_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    admin_user_id: Optional[str] = Query(None, description="Filter by admin user"),
    date_from: Optional[str] = Query(None, description="ISO date string lower bound"),
    date_to: Optional[str] = Query(None, description="ISO date string upper bound"),
    admin: dict = Depends(require_admin),
):
    """Paginated audit log, newest first. Filters: action_type, admin_user_id, date range."""
    return get_audit_log(
        page=page,
        limit=limit,
        action_filter=action_type,
        admin_filter=admin_user_id,
        date_from=date_from,
        date_to=date_to,
    )


# ─── Reports ─────────────────────────────────────────────────────────────────

@router.get("/reports")
def admin_reports(
    report_type: str = Query("weekly", regex="^(daily|weekly)$"),
    limit: int = Query(12, ge=1, le=52),
    admin: dict = Depends(require_admin),
):
    """Returns last N reports of the given type, newest first."""
    return get_reports(report_type=report_type, limit=limit)
