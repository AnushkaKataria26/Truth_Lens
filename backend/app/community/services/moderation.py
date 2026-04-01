import uuid
import logging
from app.models.db_models import Post, User

logger = logging.getLogger(__name__)

def evaluate_post_for_moderation(post: Post):
    # Auto-flagging rules (run after every post creation):
    flagged = False
    
    # 1. If post.report_count >= 5 → add to admin moderation queue
    if getattr(post, "report_count", 0) >= 5:
        flagged = True
        logger.info(f"Post {post.id} flagged: report count >= 5")
        
    # 2. If post.authenticity_score > 85 but post title contains alarm words
    #    (list: ["BREAKING", "EXPOSED", "SHOCKING", "LEAKED"]) → flag for review
    #    (possible misuse: posting authentic media with misleading title)
    alarm_words = ["BREAKING", "EXPOSED", "SHOCKING", "LEAKED"]
    title_upper = post.title.upper() if post.title else ""
    
    if getattr(post, "authenticity_score", 0.0) > 85.0:
        if any(word in title_upper for word in alarm_words):
            flagged = True
            logger.info(f"Post {post.id} flagged: high authenticity with alarm words")
            
    # 3. If same user posts > 10 times in 1 hour → rate-limit + flag account
    # [MOCK] checking rate limits
    user_post_count = 2 # mock
    if user_post_count > 10:
        logger.warning(f"User {post.user_id} flagged: >10 posts in 1 hour")
        
    if flagged:
        # Moderation queue stored in Redis sorted set:
        # [MOCK] ZADD "moderation:queue" <report_count> <post_id>
        # redis_client.zadd("moderation:queue", {str(post.id): post.report_count})
        logger.info(f"Added post {post.id} to moderation queue")
        
    return flagged

# Admin actions:
# POST /api/v1/admin/moderation/posts/{post_id}/remove
def remove_post(post_id: uuid.UUID):
    # Soft delete
    pass

# POST /api/v1/admin/moderation/posts/{post_id}/override_risk
def override_risk(post_id: uuid.UUID, new_risk: str):
    pass

# POST /api/v1/admin/moderation/users/{user_id}/ban
def ban_user(user_id: uuid.UUID):
    pass

# GET /api/v1/admin/moderation/queue — paginated moderation queue
def get_moderation_queue(skip: int = 0, limit: int = 50):
    # Admin retrieves via: ZREVRANGE "moderation:queue" 0 49
    return []
    
# GET /api/v1/admin/stats — platform-wide stats for admin dashboard
def get_admin_stats():
    return {}
