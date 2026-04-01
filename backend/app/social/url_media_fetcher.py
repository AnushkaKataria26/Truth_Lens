import os
import glob
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Retry configuration for yt-dlp (exponential backoff)
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # seconds

# Platform detection patterns
PLATFORM_PATTERNS = {
    "twitter": ["twitter.com", "x.com", "t.co"],
    "reddit": ["reddit.com", "redd.it"],
    "facebook": ["facebook.com", "fb.com", "fb.watch"],
    "instagram": ["instagram.com", "instagr.am"],
    "youtube": ["youtube.com", "youtu.be"],
    "tiktok": ["tiktok.com"],
}


@dataclass
class URLFetchResult:
    media_file_path: Optional[str] = None
    platform: str = "unknown"
    original_title: Optional[str] = None
    original_description: Optional[str] = None
    upload_timestamp: Optional[float] = None        # Unix timestamp
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    original_url: Optional[str] = None
    location_tag: Optional[str] = None              # platform-specific location
    error: Optional[str] = None


def detect_platform(url: str) -> str:
    """Detect social media platform from URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    host = host.lower().replace("www.", "")

    for platform, domains in PLATFORM_PATTERNS.items():
        if any(d in host for d in domains):
            return platform
    return "unknown"


def _find_downloaded_file(output_dir: str) -> Optional[str]:
    """Find the downloaded media file in the output directory."""
    for ext in ["*.mp4", "*.webm", "*.mkv", "*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp3", "*.wav"]:
        files = glob.glob(os.path.join(output_dir, ext))
        if files:
            return max(files, key=os.path.getmtime)
    all_files = [f for f in glob.glob(os.path.join(output_dir, "*"))
                 if not f.endswith(".json") and os.path.isfile(f)]
    return max(all_files, key=os.path.getmtime) if all_files else None


def _download_with_retry(ydl_opts: dict, post_url: str) -> dict:
    """
    Download media with exponential backoff retry logic.
    Max 3 attempts, delays: 2s, 4s, 8s.
    On final failure, raises the last exception.
    """
    import yt_dlp

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(post_url, download=True)
            return info
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"yt-dlp attempt {attempt + 1}/{MAX_RETRIES} failed for {post_url}: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"yt-dlp all {MAX_RETRIES} attempts failed for {post_url}: {e}"
                )
    raise last_error


def fetch_media_from_url(post_url: str, job_id: str) -> URLFetchResult:
    """
    Download media from a social media post URL using yt-dlp.
    Supports: Twitter/X, Reddit, Facebook, Instagram, YouTube, TikTok, direct media URLs.

    Uses exponential backoff retry logic (max 3 attempts, delays: 2s, 4s, 8s).
    On final failure, returns URLFetchResult with error flag.
    """
    output_path = f"/tmp/{job_id}/url_media"
    os.makedirs(output_path, exist_ok=True)

    platform = detect_platform(post_url)

    try:
        import yt_dlp  # noqa: F401 — verify import before retry loop

        ydl_opts = {
            "outtmpl": f"{output_path}/%(title).100s.%(ext)s",
            "format": "best[filesize<200M]",         # enforce 200MB size limit
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writeinfojson": True,                    # save metadata JSON alongside media
            "socket_timeout": 30,
            # NOTE: yt-dlp's built-in retries handle HTTP errors;
            # our _download_with_retry handles platform rate-limiting & transient failures
            "retries": 3,
        }

        info = _download_with_retry(ydl_opts, post_url)
        media_path = _find_downloaded_file(output_path)

        result = URLFetchResult(
            media_file_path=media_path,
            platform=platform,
            original_title=info.get("title"),
            original_description=info.get("description"),
            upload_timestamp=info.get("timestamp"),
            uploader=info.get("uploader"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            comment_count=info.get("comment_count"),
            original_url=info.get("webpage_url", post_url),
            location_tag=info.get("location"),
        )

        logger.info(
            f"Fetched media from {platform}: {media_path} "
            f"views={result.view_count} likes={result.like_count}"
        )
        return result

    except ImportError:
        logger.error("yt-dlp not installed. Cannot fetch media from URL.")
        return URLFetchResult(platform=platform, error="yt-dlp not installed")
    except Exception as e:
        logger.error(f"yt-dlp fetch failed for {post_url} after {MAX_RETRIES} retries: {e}")
        return URLFetchResult(platform=platform, error=str(e))


def url_fetch_to_dict(result: URLFetchResult) -> dict:
    """Serialize URLFetchResult for API response."""
    return asdict(result)
