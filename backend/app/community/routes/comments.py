from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.auth.jwt_handler import get_current_user

router = APIRouter(prefix="/api/v1/community/posts", tags=["community comments"])

class CommentCreate(BaseModel):
    body: str = Field(..., max_length=500)
    parent_comment_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    body: str

@router.post("/{post_id}/comments")
def create_comment(post_id: str, data: CommentCreate, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    
    # [MOCK] DB Validations
    if data.parent_comment_id:
        # Check if parent exists
        parent_exists = True # mock DB check
        if not parent_exists:
            raise HTTPException(status_code=404, detail="Parent comment not found")
            
        # Check nesting level (max 1 level deep)
        parent_has_parent = False # mock DB check: parent_comment.parent_comment_id is not None
        if parent_has_parent:
            raise HTTPException(status_code=400, detail="Maximum comment nesting depth reached")
            
    # [MOCK] Create Comment in DB
    comment_id = str(uuid.uuid4())
    
    # [MOCK] Increment post.comment_count in DB
    # post = db.query(Post).filter(Post.id == post_id).first()
    # post.comment_count += 1
    # db.commit()
    
    return CommentResponse(
        id=comment_id,
        body=data.body
    )
