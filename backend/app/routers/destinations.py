from fastapi import APIRouter
from typing import Optional
from app.database import db

router = APIRouter(prefix="/destinations", tags=["Destinations"])

# Fetch destinations within 50-kilometer (50000 meters) radius; if isolated completely, get `limit` closest
@router.get("/near")
def get_nearby(lat: float, lng: float, category: Optional[str] = None, price_tier: Optional[str] = None, limit: int = 5):
    filters = {}
    if category: filters["category"] = category
    if price_tier: filters["price_tier"] = price_tier

    query_local = {
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": 50000
            }
        },
        **filters
    }

    results = list(db.mongo_db.destinations.find(
        query_local, 
        {"_id": 1, "location": 1, "name": 1, "category": 1, "price_tier": 1}
    ).limit(limit))
    
    warning_flag = False

    # Query 1 returns [] => execute Query 2
    if not results:
        warning_flag = True
        query_global = {
            "location": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [lng, lat]}
                }
            },
            **filters
        }
        results = list(db.mongo_db.destinations.find(
            query_global, 
            {"_id": 1, "location": 1, "name": 1, "category": 1, "price_tier": 1}
        ).limit(limit))

    # Data Hydration
    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return {
        "results": destinations,
        "is_sparse_area": warning_flag,
        "message": "Showing closest results globally" if warning_flag else "Showing results within 50km"
    }


# When client clicks READ MORE about destination, log destination in Redis RAM to incr and track destination popularity
@router.post("/{destination_id}/visit", status_code=201)
def log_destination_visit(destination_id: str):
    db.redis_client.zincrby("trending_destinations", 1, destination_id)
    db.redis_client.delete("trending:top:10")  # delete top 10 trending cache key; to be rebuilt due to new incr
    # Above line forces us to make `trending:top:10` our go-to cache; we can then serve part or all of the 10 objects given
    return {"status": "visit logged", "destination_id": destination_id}
