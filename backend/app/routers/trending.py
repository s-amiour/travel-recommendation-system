import json
from fastapi import APIRouter
from app.database import db

router = APIRouter(prefix="/trending", tags=["Trending"])


"""
    Retrieve most visited locations.

    Utilizes "Cache-Aside" & "Read-Through" pattern to prevent stressing Redis sorted set CPU on every single page load.
    Acts as the cold start fallback recommendations, i.e. when client registers for first time.

    Parameters:
    limit (int): The number of top trending destinations to retrieve.
    
    Returns:
    list: Objects each containing destination ID alongside popularity score.

"""
@router.get("/")
def get_trending_destinations(limit: int = 10):
    # Cache-Aside pattern
    cache_key = f"trending:top:{limit}"

    cached_result = db.redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # If cache misses, it queries the trending_destinations sorted set.
    # ZREVRANGE returns them sorted from highest score to lowest score.
    trending = db.redis_client.zrevrange(
        "trending_destinations",
        0,
        limit - 1,
        withscores=True
    )

    result = [
        {
            "destination_id": destination_id,
            "score": score
        }
        for destination_id, score in trending
    ]

    # Recaches the trending destinations list for 1 hour 
    db.redis_client.setex(cache_key, 3600, json.dumps(result))

    return result