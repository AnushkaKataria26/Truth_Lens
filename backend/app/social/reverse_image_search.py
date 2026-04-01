import os
import json
import base64
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# ─── Demo Mode Static Data ────────────────────────────────────────────────────


@dataclass
class ReverseSearchResult:
    similar_images_found: int = 0
    top_matches: list = field(default_factory=list)
    recontextualized_flag: bool = False
    old_image_reposted_flag: bool = False
    original_source_urls: list = field(default_factory=list)
    error: Optional[str] = None


def _get_demo_result() -> ReverseSearchResult:
    """Return static mock data in DEMO_MODE (SerpAPI free tier: 100 searches/month)."""
    return ReverseSearchResult(
        similar_images_found=3,
        top_matches=[
            {"title": "Original news article", "link": "https://example.com/original",
             "source": "Example News", "thumbnail": ""},
            {"title": "Shared on social media", "link": "https://example.com/repost",
             "source": "Social Platform", "thumbnail": ""},
            {"title": "Fact check analysis", "link": "https://example.com/factcheck",
             "source": "FactCheck.org", "thumbnail": ""},
        ],
        recontextualized_flag=False,
        old_image_reposted_flag=False,
        original_source_urls=[
            "https://example.com/original",
            "https://example.com/repost",
            "https://example.com/factcheck",
        ],
    )


# ─── Perceptual Hash Cache ────────────────────────────────────────────────────

def _compute_phash(image_path: str) -> Optional[str]:
    """
    Compute perceptual hash of image using imagehash (pHash algorithm).
    Used as Redis cache key — same image won't be re-queried within 24h.
    """
    try:
        import imagehash
        from PIL import Image
        img = Image.open(image_path)
        return str(imagehash.phash(img))
    except ImportError:
        logger.warning("imagehash/Pillow not installed — cache disabled")
        return None
    except Exception as e:
        logger.warning(f"pHash computation failed: {e}")
        return None


def _get_cached_result(phash: str) -> Optional[ReverseSearchResult]:
    """Check Redis for cached reverse search result by perceptual hash."""
    try:
        import redis
        r = redis.Redis.from_url(REDIS_URL)
        cached = r.get(f"reverse_search:{phash}")
        if cached:
            data = json.loads(cached)
            logger.info(f"Cache HIT for pHash={phash}")
            return ReverseSearchResult(**data)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")
    return None


def _cache_result(phash: str, result: ReverseSearchResult):
    """Cache reverse search result in Redis by pHash, TTL=24h."""
    try:
        import redis
        r = redis.Redis.from_url(REDIS_URL)
        r.setex(
            f"reverse_search:{phash}",
            86400,  # 24 hours TTL
            json.dumps(asdict(result)),
        )
        logger.info(f"Cached reverse search for pHash={phash} (TTL=86400s)")
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")


# ─── Core Functions ───────────────────────────────────────────────────────────

def _caption_mismatch(caption_a: str, caption_b: str, threshold: float = 0.20) -> bool:
    """Check if two captions have < threshold token overlap."""
    if not caption_a or not caption_b:
        return False

    tokens_a = set(caption_a.lower().split())
    tokens_b = set(caption_b.lower().split())

    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "is", "and", "or", "with"}
    tokens_a -= stop_words
    tokens_b -= stop_words

    if not tokens_a or not tokens_b:
        return False

    overlap = len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))
    return overlap < threshold


def _is_significantly_older(match_date_str: str, post_date: Optional[datetime], days: int = 180) -> bool:
    """Check if match source date is significantly older than post date."""
    if not post_date:
        return False
    try:
        for fmt in ["%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%dT%H:%M:%S"]:
            try:
                match_date = datetime.strptime(match_date_str.strip(), fmt)
                return (post_date - match_date).days > days
            except ValueError:
                continue
    except Exception:
        pass
    return False


def extract_thumbnail(media_path: str) -> str:
    """Extract a thumbnail from video; for images, returns path as-is."""
    if not media_path:
        return media_path

    video_exts = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv"}
    _, ext = os.path.splitext(media_path)
    if ext.lower() not in video_exts:
        return media_path

    thumb_path = media_path.rsplit(".", 1)[0] + "_thumb.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-i", media_path, "-ss", "00:00:01", "-vframes", "1",
             "-q:v", "2", thumb_path, "-y", "-loglevel", "error"],
            timeout=10, check=True,
        )
        return thumb_path
    except Exception as e:
        logger.warning(f"Thumbnail extraction failed: {e}")
        return media_path


def reverse_image_search(
    image_path: str,
    current_caption: Optional[str] = None,
    post_date: Optional[datetime] = None,
) -> ReverseSearchResult:
    """
    Reverse image search using SerpAPI Google Lens endpoint.
    Flags: recontextualized media, old image reposted as new.

    Optimizations:
    - DEMO_MODE: returns static mock data (SerpAPI free tier = 100/month)
    - Production: caches by perceptual hash (pHash) in Redis, TTL=24h
    """
    # ── DEMO_MODE bypass is disabled to ensure REAL data is fetched from APIs ──
    if DEMO_MODE:
        logger.info("DEMO_MODE is active, but mock results are disabled. Proceeding with real search.")

    if not SERPAPI_KEY:
        logger.warning("SERPAPI_API_KEY not set — returning empty results")
        return ReverseSearchResult(error="SERPAPI_API_KEY not configured")

    # ── Check pHash cache ──
    phash = _compute_phash(image_path)
    if phash:
        cached = _get_cached_result(phash)
        if cached:
            return cached

    try:
        import serpapi

        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode()

        client = serpapi.Client(api_key=SERPAPI_KEY)
        results = client.search({
            "engine": "google_lens",
            "image_data": image_b64,
            "hl": "en",
        })

        visual_matches = results.get("visual_matches", [])[:10]

        recontextualized = False
        old_image_reposted = False
        original_source_urls = []

        for match in visual_matches:
            match_title = match.get("title", "")
            match_link = match.get("link", "")
            match_date = match.get("date", "")

            original_source_urls.append(match_link)

            if current_caption and _caption_mismatch(current_caption, match_title, threshold=0.20):
                recontextualized = True

            if match_date and _is_significantly_older(match_date, post_date, days=180):
                old_image_reposted = True

        result = ReverseSearchResult(
            similar_images_found=len(visual_matches),
            top_matches=[
                {
                    "title": m.get("title", ""),
                    "link": m.get("link", ""),
                    "source": m.get("source", ""),
                    "thumbnail": m.get("thumbnail", ""),
                }
                for m in visual_matches[:5]
            ],
            recontextualized_flag=recontextualized,
            old_image_reposted_flag=old_image_reposted,
            original_source_urls=original_source_urls,
        )

        # ── Cache result by pHash ──
        if phash:
            _cache_result(phash, result)

        logger.info(
            f"Reverse search: {len(visual_matches)} matches, "
            f"recontextualized={recontextualized}, old_repost={old_image_reposted}"
        )
        return result

    except ImportError:
        logger.error("serpapi not installed")
        return ReverseSearchResult(error="serpapi not installed")
    except Exception as e:
        logger.error(f"Reverse image search failed: {e}")
        return ReverseSearchResult(error=str(e))


def reverse_search_to_dict(result: ReverseSearchResult) -> dict:
    """Serialize ReverseSearchResult for API response."""
    return asdict(result)
