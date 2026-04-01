from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel, HttpUrl
import uuid
import os
from typing import Literal

from app.models.schemas import UploadResponse

router = APIRouter(tags=["upload"])

# Mock dependencies for now
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "mp4,mov,avi,jpg,jpeg,png,webp,wav,mp3,m4a").split(",")

class URLUploadRequest(BaseModel):
    url: HttpUrl

def get_media_type(filename: str) -> Literal["video", "image", "audio", "text"]:
    ext = filename.split(".")[-1].lower()
    if ext in ["mp4", "mov", "avi"]: return "video"
    if ext in ["jpg", "jpeg", "png", "webp"]: return "image"
    if ext in ["wav", "mp3", "m4a"]: return "audio"
    return "text"

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Validate extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
        
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Check Content-Length header if available
    # Actually FastAPI does not inject request directly here, assuming Content-Length was checked by middleware or we just use streaming byte counter.
    
    file_size_bytes = 0
    while chunk := file.file.read(8192):
        file_size_bytes += len(chunk)
        if file_size_bytes > max_bytes:
            raise HTTPException(status_code=400, detail=f"File exceeds max size of {MAX_FILE_SIZE_MB}MB during streaming")
            
    file.file.seek(0)
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    job_id = uuid.uuid4()
    
    # [MOCK] Upload raw file to S3 under key: media/{job_id}/{filename}
    # [MOCK] Creates DB record with status="uploaded"
    # [MOCK] Publishes job_id to Redis queue
    
    return UploadResponse(
        job_id=job_id,
        media_url=f"s3://truthlens-media/media/{job_id}/{file.filename}",
        media_type=get_media_type(file.filename),
        file_size_mb=round(file_size_mb, 2),
        status="uploaded"
    )

@router.post("/upload/url", response_model=UploadResponse)
async def upload_from_url(request: URLUploadRequest):
    # [MOCK] Downloads media from URL, validates, uploads to S3, same flow
    job_id = uuid.uuid4()
    
    return UploadResponse(
        job_id=job_id,
        media_url=f"s3://truthlens-media/media/{job_id}/downloaded_file",
        media_type="video",  # Mocked
        file_size_mb=0.0,    # Mocked
        status="uploaded"
    )
