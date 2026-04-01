import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional

from app.auth.jwt_handler import get_current_user
from app.provenance.c2pa_parser import parse_c2pa, c2pa_to_dict
from app.provenance.exif_parser import parse_exif, exif_to_dict
from app.provenance.provenance_scorer import compute_provenance_score, provenance_to_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/provenance", tags=["provenance"])


# ─── Response Models ──────────────────────────────────────────────────────────

class ProvenanceCheckResponse(BaseModel):
    c2pa: dict
    exif: dict
    provenance_score: dict
    flags: list


class ProvenanceCheckByJobResponse(BaseModel):
    job_id: str
    c2pa: dict
    exif: dict
    provenance_score: dict
    flags: list


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/check", response_model=ProvenanceCheckResponse)
async def check_provenance(
    file: UploadFile = File(...),
    media_type: str = Query("image", regex="^(image|video|audio)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a media file and run C2PA + EXIF provenance analysis.
    Returns provenance score, C2PA details, EXIF data, and all flags.
    """
    # Save uploaded file to temp location
    tmp_path = f"/tmp/provenance_{file.filename}"
    try:
        contents = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(contents)

        # Run C2PA parsing
        c2pa_result = parse_c2pa(tmp_path)

        # Run EXIF parsing
        exif_result = parse_exif(tmp_path, media_type)

        # Compute combined provenance score
        score = compute_provenance_score(c2pa_result, exif_result)

        return ProvenanceCheckResponse(
            c2pa=c2pa_to_dict(c2pa_result),
            exif=exif_to_dict(exif_result),
            provenance_score=provenance_to_dict(score),
            flags=score.flags,
        )
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/check/{job_id}", response_model=ProvenanceCheckByJobResponse)
def check_provenance_by_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Run provenance check on a previously uploaded analysis job.
    Fetches the media file from S3 by job_id.
    """
    # [MOCK] In production:
    # job = db.query(AnalysisJob).filter_by(id=job_id, user_id=current_user["sub"]).first()
    # if not job: raise HTTPException(404)
    # file_path = download_from_s3(job.s3_key) → tmp path

    # Mock result
    from app.provenance.c2pa_parser import C2PAResult
    from app.provenance.exif_parser import EXIFResult

    mock_c2pa = C2PAResult(present=False, valid=False)
    mock_exif = EXIFResult(flags=[], raw_tags={})
    mock_score = compute_provenance_score(mock_c2pa, mock_exif)

    return ProvenanceCheckByJobResponse(
        job_id=job_id,
        c2pa=c2pa_to_dict(mock_c2pa),
        exif=exif_to_dict(mock_exif),
        provenance_score=provenance_to_dict(mock_score),
        flags=mock_score.flags,
    )


@router.get("/c2pa/{job_id}")
def get_c2pa_details(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns raw C2PA manifest details for a job.
    Includes full edit history, ingredients, and signer info.
    """
    # [MOCK]
    return {
        "job_id": job_id,
        "c2pa_present": False,
        "c2pa_valid": False,
        "details": None,
    }


@router.get("/exif/{job_id}")
def get_exif_details(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns raw EXIF/metadata for a job.
    Includes all extracted tags, GPS, device info, and anomaly flags.
    """
    # [MOCK]
    return {
        "job_id": job_id,
        "exif": {
            "gps_coordinates": None,
            "creation_date": None,
            "software": None,
            "device_make": None,
            "device_model": None,
            "flags": [],
            "raw_tags": {},
        },
    }
