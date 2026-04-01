from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

class UploadResponse(BaseModel):
    job_id: UUID
    media_url: str
    media_type: Literal["video", "image", "audio", "text"]
    file_size_mb: float
    status: Literal["uploaded", "queued"]

class AnalysisRequest(BaseModel):
    job_id: UUID
    user_id: Optional[str] = None

class ModalityScore(BaseModel):
    modality: Literal["visual", "audio", "text", "crossmodal"]
    confidence: float = Field(ge=0.0, le=1.0)
    flags: list[str]          # e.g. ["face_swap_detected", "frequency_cutoff_8khz"]
    weight: float             # weight used in fusion

class HeatmapData(BaseModel):
    available: bool
    s3_url: Optional[str] = None
    affected_regions: Optional[list[dict]] = None  # [{x, y, intensity}]

class SpectrogramData(BaseModel):
    available: bool
    s3_url: Optional[str] = None
    anomaly_timestamps: Optional[list[float]] = None  # seconds

class AnalysisResult(BaseModel):
    job_id: UUID
    status: Literal["queued", "processing", "complete", "failed"]
    authenticity_score: Optional[float] = None      # 0-100
    risk_level: Optional[Literal["high", "medium", "authentic"]] = None
    modality_scores: Optional[list[ModalityScore]] = None
    heatmap: Optional[HeatmapData] = None
    spectrogram: Optional[SpectrogramData] = None
    explanation: Optional[str] = None
    fact_check_results: Optional[list[dict]] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress_step: Optional[str] = None  # current pipeline step name
    progress_percent: Optional[int] = None
