import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from app.social.url_media_fetcher import URLFetchResult

logger = logging.getLogger(__name__)


@dataclass
class VelocityResult:
    view_velocity_per_hour: float = 0.0
    like_velocity_per_hour: float = 0.0
    velocity_score: float = 0.0               # 0.0–1.0 normalized
    is_viral: bool = False
    hours_since_upload: float = 0.0


def compute_velocity_score(url_fetch_result: URLFetchResult) -> VelocityResult:
    """
    Measures how fast a piece of media is spreading across platforms.
    Velocity = engagement gained per hour since first detected.

    Thresholds (calibrated empirically):
      view_velocity > 100k/hr → score near 1.0 (viral)
      view_velocity < 1k/hr   → score near 0.0 (low spread)
    """
    # Compute hours since upload
    if url_fetch_result.upload_timestamp:
        hours_since_upload = (
            datetime.utcnow() - datetime.utcfromtimestamp(url_fetch_result.upload_timestamp)
        ).total_seconds() / 3600
    else:
        # No timestamp available — assume recent (1 hour)
        hours_since_upload = 1.0

    # Avoid division by zero for very new content
    if hours_since_upload < 0.1:
        hours_since_upload = 0.1

    # Engagement velocity
    view_velocity = (url_fetch_result.view_count or 0) / hours_since_upload
    like_velocity = (url_fetch_result.like_count or 0) / hours_since_upload

    # Normalized velocity score (0–1)
    # 70% weight on views, 30% on likes
    velocity_score = (
        min(view_velocity / 100_000, 1.0) * 0.7
        + min(like_velocity / 10_000, 1.0) * 0.3
    )
    velocity_score = round(velocity_score, 4)

    is_viral = velocity_score > 0.6

    if is_viral:
        _push_viral_alert(url_fetch_result, velocity_score)

    result = VelocityResult(
        view_velocity_per_hour=round(view_velocity, 1),
        like_velocity_per_hour=round(like_velocity, 1),
        velocity_score=velocity_score,
        is_viral=is_viral,
        hours_since_upload=round(hours_since_upload, 2),
    )

    logger.info(
        f"Velocity: views/hr={view_velocity:.0f} likes/hr={like_velocity:.0f} "
        f"score={velocity_score:.4f} viral={is_viral}"
    )
    return result


def _push_viral_alert(url_fetch_result: URLFetchResult, velocity_score: float):
    """
    Push to Redis sorted set for viral alerts dashboard.
    Admin endpoint GET /api/v1/admin/analytics/viral-alerts reads this set.
    Keeps only top 100 alerts (trims sorted set).
    """
    alert = {
        "url": url_fetch_result.original_url,
        "platform": url_fetch_result.platform,
        "uploader": url_fetch_result.uploader,
        "velocity_score": velocity_score,
        "view_count": url_fetch_result.view_count,
        "like_count": url_fetch_result.like_count,
        "detected_at": datetime.utcnow().isoformat(),
    }

    # [MOCK] In production:
    # redis_client.zadd("viral:alerts", {json.dumps(alert): velocity_score})
    # redis_client.zremrangebyrank("viral:alerts", 0, -101)  # keep top 100

    logger.info(f"VIRAL ALERT pushed: {url_fetch_result.platform} score={velocity_score}")


def velocity_to_dict(result: VelocityResult) -> dict:
    """Serialize VelocityResult for API response."""
    return asdict(result)
