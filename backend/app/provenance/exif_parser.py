import json
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False
    logger.warning("exifread not installed. EXIF parsing for images will be limited.")

# Known AI generation software signatures
AI_SOFTWARE_SIGNATURES = [
    "stable diffusion", "midjourney", "dall-e", "firefly",
    "runway", "pika", "sora", "kling", "heygen",
    "deepfacelab", "faceswap", "synthesia", "d-id",
    "elevenlabs", "murf.ai",
]


@dataclass
class EXIFResult:
    gps_coordinates: Optional[tuple] = None    # (lat, lon) or None
    creation_date: Optional[str] = None
    software: Optional[str] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    flags: list = field(default_factory=list)
    raw_tags: dict = field(default_factory=dict)


def _parse_datetime(date_str: str) -> Optional[datetime]:
    """Try common EXIF date formats."""
    for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def _parse_image_exif(file_path: str) -> tuple[dict, dict]:
    """Extract EXIF tags from image using exifread."""
    if not EXIFREAD_AVAILABLE:
        return {}, {}

    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        return tags, {str(k): str(v) for k, v in tags.items()}
    except Exception as e:
        logger.warning(f"EXIF read error for {file_path}: {e}")
        return {}, {}


def _parse_video_metadata(file_path: str) -> tuple[dict, dict]:
    """Extract metadata from video using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", file_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        probe = json.loads(result.stdout) if result.returncode == 0 else {}
        fmt_tags = probe.get("format", {}).get("tags", {})
        return fmt_tags, fmt_tags
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"ffprobe error for {file_path}: {e}")
        return {}, {}


def parse_exif(file_path: str, media_type: str) -> EXIFResult:
    """
    Extract EXIF/metadata from media files and flag anomalies.
    Supports images (exifread) and videos (ffprobe).
    """
    flags = []
    gps_lat = gps_lon = None
    date_time_original = None
    software = None
    make = model_tag = None

    if media_type in ("image", "photo"):
        tags, raw = _parse_image_exif(file_path)

        gps_lat = tags.get("GPS GPSLatitude")
        gps_lon = tags.get("GPS GPSLongitude")
        date_time_original = tags.get("EXIF DateTimeOriginal")
        software = tags.get("Image Software")
        make = tags.get("Image Make")
        model_tag = tags.get("Image Model")

        # Flag: No EXIF data at all on JPEG (stripped — common in re-saved deepfakes)
        if not tags and file_path.lower().endswith((".jpg", ".jpeg")):
            flags.append("exif_stripped")

    elif media_type == "video":
        tags, raw = _parse_video_metadata(file_path)
        date_time_original = tags.get("creation_time")
        software = tags.get("encoder")
        raw = tags
    else:
        tags, raw = {}, {}

    # ── Anomaly Detection ──

    # Flag: Software contains known AI generation tool signatures
    if software and any(sig in str(software).lower() for sig in AI_SOFTWARE_SIGNATURES):
        flags.append("ai_generation_software_detected")

    # Flag: Creation date is in the future
    if date_time_original:
        parsed_date = _parse_datetime(str(date_time_original))
        if parsed_date and parsed_date > datetime.utcnow():
            flags.append("future_creation_date")

    # Flag: GPS location present (useful for geo cross-check in provenance_scorer)
    # Actual mismatch check is done in provenance_scorer.py with social context data

    result = EXIFResult(
        gps_coordinates=(str(gps_lat), str(gps_lon)) if gps_lat and gps_lon else None,
        creation_date=str(date_time_original) if date_time_original else None,
        software=str(software) if software else None,
        device_make=str(make) if make else None,
        device_model=str(model_tag) if model_tag else None,
        flags=flags,
        raw_tags=raw if isinstance(raw, dict) else {},
    )

    logger.info(f"EXIF parsed: flags={flags} software={software} device={make}/{model_tag}")
    return result


def exif_to_dict(result: EXIFResult) -> dict:
    """Serialize EXIFResult for API response."""
    return asdict(result)
