from fastapi import APIRouter, Depends, HTTPException, Query
import uuid

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])

@router.get("")
def get_leaderboard(
    period: str = Query("weekly", regex="^(weekly|monthly|alltime)$"),
    limit: int = Query(50, le=100)
):
    # For "alltime": ORDER BY users.trust_index DESC LIMIT limit
    # For "weekly"/"monthly": 
    #   Compute trust delta within period from contribution_events log table
    #   ORDER BY delta DESC — shows fastest-rising contributors
    # Cache in Redis: "leaderboard:{period}" TTL=300s
    
    # Return: list of LeaderboardEntry(rank, username, trust_index, badge, analyses_count, debunk_impact)
    # debunk_impact: count of user's high-risk posts that were later confirmed accurate
    
    mock_entry = {
        "rank": 1,
        "username": "truth_sleuth",
        "trust_index": 95.5,
        "badge": "community_educator",
        "analyses_count": 142,
        "debunk_impact": 18
    }
    
    return [mock_entry]
