import os
import requests
import json
import uuid
import subprocess
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    import serpapi
    HAS_SERPAPI = True
except ImportError:
    HAS_SERPAPI = False

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

from app.models.db_models import Base, TrainingData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./truthlens_train.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dataset")

# Modality directories
MODALITIES = ["image", "audio", "video", "text"]
for mod in MODALITIES:
    os.makedirs(os.path.join(DATASET_DIR, mod, "real"), exist_ok=True)
    os.makedirs(os.path.join(DATASET_DIR, mod, "fake"), exist_ok=True)

def download_file(url: str, dest_path: str) -> bool:
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
    return False

def download_video_or_audio(url: str, dest_path: str, extract_audio: bool = False) -> bool:
    if not HAS_YTDLP:
        logger.warning("yt-dlp is not installed. Cannot download video/audio from YouTube.")
        return False
    
    ydl_opts = {
        'outtmpl': dest_path,
        'quiet': True,
        'no_warnings': True,
    }
    if extract_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.warning(f"Failed to extract media via yt-dlp from {url}: {e}")
    return False

def save_to_db(media_url, source_url, label, modality, local_path=None, text_content=None):
    db = SessionLocal()
    entry = TrainingData(
        media_url=media_url,
        source_url=source_url,
        label=label,
        modality=modality,
        local_path=local_path,
        text_content=text_content
    )
    db.add(entry)
    db.commit()
    db.close()
    logger.info(f"Saved {label} {modality} entry: {local_path if local_path else 'Text Content'}")

# --- Image Fetching ---
def fetch_images(limit: int = 5):
    if not HAS_SERPAPI or not SERPAPI_KEY:
        return
    client = serpapi.Client(api_key=SERPAPI_KEY)
    
    # Real Images
    res_real = client.search({"engine": "google_images", "q": "latest news authentic raw photos 2024", "ijn": "0"})
    for i, img in enumerate(res_real.get("images_results", [])[:limit]):
        url = img.get("original")
        if url:
            path = os.path.join(DATASET_DIR, "image", "real", f"{uuid.uuid4()}.jpg")
            if download_file(url, path):
                save_to_db(url, img.get("link"), "real", "image", path)

    # Fake Images
    res_fake = client.search({"engine": "google_images", "q": "midjourney generated artificial face deepfake", "ijn": "0"})
    for i, img in enumerate(res_fake.get("images_results", [])[:limit]):
        url = img.get("original")
        if url:
            path = os.path.join(DATASET_DIR, "image", "fake", f"{uuid.uuid4()}.jpg")
            if download_file(url, path):
                save_to_db(url, img.get("link"), "fake", "image", path)

# --- Text Fetching ---
def fetch_texts(limit: int = 5):
    if not HAS_SERPAPI or not SERPAPI_KEY:
        return
    client = serpapi.Client(api_key=SERPAPI_KEY)
    
    # Real Text (Google News)
    res_real = client.search({"engine": "google", "q": "latest breaking news today", "tbm": "nws"})
    for i, news in enumerate(res_real.get("news_results", [])[:limit]):
        text = f"{news.get('title', '')}. {news.get('snippet', '')}"
        link = news.get("link")
        if text.strip():
            save_to_db(None, link, "real", "text", text_content=text)

    # Fake Text (Known Misinformation Queries)
    res_fake = client.search({"engine": "google", "q": "known fake news examples disjointed false claims", "tbm": "nws"})
    for i, news in enumerate(res_fake.get("news_results", [])[:limit]):
        text = f"{news.get('title', '')}. {news.get('snippet', '')}"
        link = news.get("link")
        if text.strip():
            save_to_db(None, link, "fake", "text", text_content=text)

# --- Media Extraction Helper ---
def fetch_media(query: str, label: str, modality: str, extract_audio: bool, ext: str, limit: int = 2):
    if not HAS_SERPAPI or not SERPAPI_KEY:
        return
    client = serpapi.Client(api_key=SERPAPI_KEY)
    res = client.search({"engine": "google", "q": query, "tbm": "vid"})
    
    results = res.get("video_results", [])
    count = 0
    for vid in results:
        if count >= limit:
            break
        link = vid.get("link")
        if link and "youtube.com" in link:
            path = os.path.join(DATASET_DIR, modality, label, f"{uuid.uuid4()}{ext}")
            if download_video_or_audio(link, path, extract_audio=extract_audio):
                save_to_db(link, link, label, modality, path)
                count += 1

# --- Audio Fetching ---
def fetch_audios(limit: int = 2):
    # Real Audio
    fetch_media("authentic news broadcast speech", "real", "audio", extract_audio=True, ext="", limit=limit)
    # Fake Audio
    fetch_media("AI voice clone deepfake speech example", "fake", "audio", extract_audio=True, ext="", limit=limit)

# --- Video Fetching ---
def fetch_videos(limit: int = 2):
    # Real Video
    fetch_media("raw footage news report short", "real", "video", extract_audio=False, ext=".mp4", limit=limit)
    # Fake Video
    fetch_media("Sora AI generated video deepfake", "fake", "video", extract_audio=False, ext=".mp4", limit=limit)

if __name__ == "__main__":
    logger.info("Starting MULTIMODAL dataset builder...")
    if not SERPAPI_KEY:
        logger.error("SERPAPI_API_KEY is not set! Aborting.")
        exit(1)
        
    logger.info("Fetching Images...")
    fetch_images(limit=5)
    
    logger.info("Fetching Texts...")
    fetch_texts(limit=5)
    
    if HAS_YTDLP:
        logger.info("Fetching Audios...")
        fetch_audios(limit=2)
        
        logger.info("Fetching Videos...")
        fetch_videos(limit=2)
    else:
        logger.warning("Skipping Audio and Video ingestion because yt-dlp is not installed. Run 'pip install yt-dlp'.")
        
    logger.info("Multimodal dataset ingestion complete.")
