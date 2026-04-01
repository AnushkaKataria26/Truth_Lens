from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid

from app.auth.jwt_handler import get_current_user
from app.community.services.trust_engine import record_contribution

router = APIRouter(prefix="/api/v1/community/reactions", tags=["community reactions"])

class ReactionCreate(BaseModel):
    target_type: str    # "post" | "comment"
    target_id: str
    reaction_type: str  # "upvote" | "bookmark" | "report"

@router.post("")
def create_reaction(data: ReactionCreate, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    # Upsert Reaction (unique constraint prevents duplicate reactions)
    
    # If reaction_type == "upvote": increment target upvote_count + trigger trust update for author
    if data.reaction_type == "upvote":
        # [MOCK] find author of target
        target_author_id = uuid.uuid4() 
        if data.target_type == "post":
            record_contribution(target_author_id, "post_upvoted")
        elif data.target_type == "comment":
            record_contribution(target_author_id, "comment_upvoted")
            
    # If reaction_type == "report": increment report_count
    #   if report_count >= 5: flag post for admin review (add to moderation queue in Redis)
    elif data.reaction_type == "report":
        # [MOCK] 
        pass
        
    # Return: {success: true, new_count: int}
    return {
        "success": True,
        "new_count": 1 # mock
    }
