import uuid
import logging

logger = logging.getLogger(__name__)

CONTRIBUTION_WEIGHTS = {
    "post_published": 5.0,
    "post_upvoted": 2.0,          # someone upvoted user's post
    "comment_upvoted": 1.0,
    "analysis_performed": 1.0,
    "debunk_confirmed": 10.0,     # admin confirms user's high-risk post was accurate
    "false_report_penalty": -5.0, # user reported content found to be authentic
    "content_removed": -10.0,     # user's post was removed by admin
}

def evaluate_and_award_badges(user_id: uuid.UUID, new_trust: float):
    # Badge award thresholds:
    #   trust_index >= 20  → "truth_seeker"
    #   trust_index >= 50  → "fact_defender"
    #   trust_index >= 80  → "community_educator"
    # Each badge awarded only once (check Badge table before inserting)
    badge_thresholds = [
        (20.0, "truth_seeker"),
        (50.0, "fact_defender"),
        (80.0, "community_educator"),
    ]
    for threshold, badge_type in badge_thresholds:
        if new_trust >= threshold:
            # [MOCK] Check if badge already awarded, insert if not
            # db.query(Badge).filter(Badge.user_id == user_id, Badge.badge_type == badge_type).first()
            logger.info(f"Badge check: user {user_id} qualifies for '{badge_type}'")

def update_trust_index(user_id: uuid.UUID, event_type: str):
    """
    Must be wrapped in a database transaction with row-level locking
    (SELECT FOR UPDATE on the user row) to prevent race conditions
    when multiple reactions arrive simultaneously for the same user.
    """
    delta = CONTRIBUTION_WEIGHTS.get(event_type, 0.0)
    if delta == 0.0:
        return

    # [MOCK] In production this is a real DB session with row-level lock:
    #
    # with db.begin():
    #     user = db.execute(
    #         select(User).where(User.id == user_id).with_for_update()
    #     ).scalar_one()
    #     user.trust_index = max(0.0, min(user.trust_index + delta, 100.0))
    #     db.commit()
    #
    # The SELECT ... FOR UPDATE ensures serialized access per user row.

    current_trust = 10.0  # mock
    new_trust = max(0.0, min(current_trust + delta, 100.0))
    logger.info(f"Trust update: user={user_id} event={event_type} delta={delta} new_trust={new_trust}")

    # Check badge thresholds after update
    evaluate_and_award_badges(user_id, new_trust)

def record_contribution(user_id: uuid.UUID, event_type: str):
    update_trust_index(user_id, event_type)
