from datetime import datetime
from typing import Optional
from app.models.db_models import Post

def compute_feed_score(post: Post, author_trust_index: float) -> float:
    # Feed scoring formula — computed at query time, not stored
    # Inspired by Hacker News ranking with trust weighting
    
    hours_since_post = (datetime.utcnow() - post.created_at).total_seconds() / 3600
    gravity = 1.8  # decay rate — tune based on desired content freshness

    engagement_score = (
        post.upvote_count * 1.0
        + post.comment_count * 1.5
        + post.bookmark_count * 0.8
        - post.report_count * 3.0   # strong penalty for reports
    )

    trust_multiplier = 1.0 + (author_trust_index / 100)  # max 2x boost for trust=100
    risk_boost = 1.3 if post.risk_level == "high" else 1.0  # high-risk posts surface faster

    score = (engagement_score * trust_multiplier * risk_boost) / ((hours_since_post + 2) ** gravity)
    return score

def get_ranked_feed(
    filters: str,
    modality: str,
    sort: str,
    limit: int,
    cursor_created_at: Optional[str] = None,
    cursor_id: Optional[str] = None,
):
    """
    Cursor-based pagination instead of offset-based.
    Cursor = last post's (created_at, id) to avoid offset performance
    degradation at high page numbers.

    In production:
        query = select(Post).where(Post.is_removed == False, Post.is_public == True)
        if cursor_created_at and cursor_id:
            query = query.where(
                (Post.created_at < cursor_created_at) |
                ((Post.created_at == cursor_created_at) & (Post.id < cursor_id))
            )
        query = query.order_by(Post.created_at.desc()).limit(limit)

    Cache ranked feed in Redis with TTL=60s per filter combination.
    Key: "feed:{filter}:{modality}:{sort}:{cursor_id}"
    """

    # [MOCK] Return empty list — production implementation queries DB
    return {
        "items": [],
        "next_cursor": None,  # { "created_at": "...", "id": "..." } when more results exist
    }
