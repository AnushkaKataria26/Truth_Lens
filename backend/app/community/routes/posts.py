from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.auth.jwt_handler import get_current_user
from app.community.services.feed_ranker import get_ranked_feed
from app.community.services.trust_engine import record_contribution

router = APIRouter(prefix="/api/v1/community/posts", tags=["community posts"])

class PostCreate(BaseModel):
    job_id: str
    title: str
    caption: Optional[str] = None
    is_public: bool = True

class PostResponse(BaseModel):
    id: str
    title: str
    authenticity_score: float
    # [MOCK] Add more fields as needed

@router.post("", response_model=PostResponse)
def create_post(data: PostCreate, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    user_id = current_user["sub"]
    
    # Validate: job_id belongs to current user, job status is "complete"
    # Pull authenticity_score, risk_level, media_thumbnail_url from analysis_results
    # Create Post record
    post_id = str(uuid.uuid4())
    
    # Trigger trust_engine.record_contribution(user_id, "post")
    record_contribution(uuid.UUID(user_id), "post_published")
    
    return PostResponse(
        id=post_id,
        title=data.title,
        authenticity_score=85.0
    )

@router.get("/feed")
def get_feed(
    limit: int = Query(20, ge=1, le=100),
    filter: str = Query("all"),
    modality: str = Query("all"),
    sort: str = Query("recent"),
    cursor_created_at: Optional[str] = Query(None, description="Cursor: created_at of last item"),
    cursor_id: Optional[str] = Query(None, description="Cursor: id of last item"),
):
    # Auth: optional (public feed visible to all)
    # Cursor-based pagination: pass last post's (created_at, id) as cursor
    feed = get_ranked_feed(filter, modality, sort, limit, cursor_created_at, cursor_id)
    return feed

@router.get("/{post_id}")
def get_post(post_id: str):
    # Return single post with full detail + top 10 comments
    return {
        "id": post_id,
        "title": "Mock Post title",
        "comments": []
    }

@router.delete("/{post_id}")
def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    # Auth: post owner or admin only
    # Soft delete: set is_removed=True
    return {"success": True}
