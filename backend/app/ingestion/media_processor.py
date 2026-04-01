from dataclasses import dataclass
from typing import Optional

from app.ingestion.keyframe_extractor import extract_keyframes
from app.ingestion.audio_extractor import extract_audio
from app.ingestion.text_extractor import extract_text, TextBundle

@dataclass
class MediaBundle:
    job_id: str
    media_type: str
    frames_paths: Optional[list[str]] = None
    audio_path: Optional[str] = None
    text_bundle: Optional[TextBundle] = None

def get_media_type_from_filename(filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    if ext in ["mp4", "mov", "avi"]: return "video"
    if ext in ["jpg", "jpeg", "png", "webp"]: return "image"
    if ext in ["wav", "mp3", "m4a"]: return "audio"
    return "text"

def process_media(s3_path: str, job_id: str, filename: str) -> MediaBundle:
    # Called at start of Celery task
    media_type = get_media_type_from_filename(filename)
    
    bundle = MediaBundle(job_id=job_id, media_type=media_type)
    
    if media_type == "video":
        bundle.frames_paths = extract_keyframes(s3_path, job_id)
        bundle.audio_path = extract_audio(s3_path, job_id)
        bundle.text_bundle = extract_text(s3_path, is_media_path=True)
    elif media_type == "image":
        # no extraction needed, pass directly to visual inference
        bundle.frames_paths = [s3_path]
    elif media_type == "audio":
        bundle.audio_path = extract_audio(s3_path, job_id)
    else:
        # Text only
        bundle.text_bundle = extract_text(s3_path, is_media_path=False)
        
    return bundle
