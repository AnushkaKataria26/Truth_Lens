import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from math import radians, cos, sin, asin, sqrt

from app.social.url_media_fetcher import fetch_media_from_url, URLFetchResult
from app.social.reverse_image_search import (
    reverse_image_search,
    extract_thumbnail,
    ReverseSearchResult,
)
from app.social.velocity_tracker import compute_velocity_score, VelocityResult

logger = logging.getLogger(__name__)


@dataclass
class ContextScanResult:
    fetch_result: Optional[dict] = None
    reverse_search: Optional[dict] = None
    velocity: Optional[dict] = None
    location_mismatch: bool = False
    suspicion_signals: list = field(default_factory=list)
    context_authenticity_score: float = 1.0        # 0.0–1.0 (higher = more authentic)
    error: Optional[str] = None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two GPS coordinates in km."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def _gps_location_mismatch(
    gps_coords: tuple,
    location_tag: str,
    tolerance_km: float = 50,
) -> bool:
    """
    Check if EXIF GPS coordinates mismatch the platform's location tag.
    Uses a basic geocoding approach — in production, call a geocoding API.
    """
    # [MOCK] In production:
    # geocode_result = geocoder.geocode(location_tag)
    # tag_lat, tag_lon = geocode_result.lat, geocode_result.lon
    # distance = _haversine_km(float(gps_coords[0]), float(gps_coords[1]), tag_lat, tag_lon)
    # return distance > tolerance_km

    # For now, always return False (no geocoding API configured)
    logger.info(f"GPS mismatch check: coords={gps_coords} tag={location_tag} — skipped (no geocoder)")
    return False


def scan_social_context(
    post_url: str,
    job_id: str,
    caption: Optional[str] = None,
) -> ContextScanResult:
    """
    Orchestrates all social context signals into a single ContextScanResult.
    Called from analysis_task.py when input is a URL (not a direct file upload).

    Pipeline:
    1. Fetch media from URL (yt-dlp)
    2. Reverse image search (SerpAPI)
    3. Velocity tracking (engagement rate)
    4. GPS vs location tag mismatch check
    5. Aggregate suspicion score
    """
    # ── Step 1: Fetch media ──
    fetch_result = fetch_media_from_url(post_url, job_id)
    if fetch_result.error:
        logger.warning(f"URL fetch failed: {fetch_result.error}")
        return ContextScanResult(
            fetch_result=asdict(fetch_result),
            error=f"Media fetch failed: {fetch_result.error}",
        )

    # ── Step 2: Reverse image search ──
    from datetime import datetime
    post_date = (
        datetime.utcfromtimestamp(fetch_result.upload_timestamp)
        if fetch_result.upload_timestamp
        else None
    )

    thumbnail_path = extract_thumbnail(fetch_result.media_file_path)
    reverse_result = reverse_image_search(
        image_path=thumbnail_path,
        current_caption=caption or fetch_result.original_title,
        post_date=post_date,
    )

    # ── Step 3: Velocity tracking ──
    velocity_result = compute_velocity_score(fetch_result)

    # ── Step 4: GPS vs location tag mismatch ──
    location_mismatch = False
    if fetch_result.location_tag and fetch_result.media_file_path:
        try:
            from app.provenance.exif_parser import parse_exif
            exif = parse_exif(fetch_result.media_file_path, "image")
            if exif.gps_coordinates:
                location_mismatch = _gps_location_mismatch(
                    exif.gps_coordinates,
                    fetch_result.location_tag,
                    tolerance_km=50,
                )
        except Exception as e:
            logger.warning(f"EXIF GPS check failed: {e}")

    # ── Step 5: Aggregate suspicion score ──
    suspicion_signals = []
    suspicion_score = 0.0

    if reverse_result.recontextualized_flag:
        suspicion_score += 0.35
        suspicion_signals.append("recontextualized_media")

    if reverse_result.old_image_reposted_flag:
        suspicion_score += 0.25
        suspicion_signals.append("old_media_reposted_as_new")

    if velocity_result.is_viral and velocity_result.velocity_score > 0.8:
        # Viral alone is not suspicious, but amplifies concern
        suspicion_score += 0.10
        suspicion_signals.append("viral_spread_detected")

    if location_mismatch:
        suspicion_score += 0.20
        suspicion_signals.append("gps_location_mismatch")

    suspicion_score = min(suspicion_score, 1.0)
    context_authenticity = round(1.0 - suspicion_score, 4)

    result = ContextScanResult(
        fetch_result=asdict(fetch_result),
        reverse_search=asdict(reverse_result),
        velocity=asdict(velocity_result),
        location_mismatch=location_mismatch,
        suspicion_signals=suspicion_signals,
        context_authenticity_score=context_authenticity,
    )

    logger.info(
        f"Social context scan: authenticity={context_authenticity} "
        f"signals={suspicion_signals} viral={velocity_result.is_viral}"
    )
    return result


def context_scan_to_dict(result: ContextScanResult) -> dict:
    """Serialize ContextScanResult for API response."""
    return asdict(result)
