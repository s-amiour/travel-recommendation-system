from fastapi import APIRouter
from app.database import db

router = APIRouter(prefix="/destinations", tags=["Destinations"])

# Fetch destinations within 50-kilometer (50000 meters) radius
@router.get("/near")
def get_nearby(lat: float, lng: float, category: str = "beach", price_tier: str = "$$$", limit: int = 20):
    results = db.mongo_db.destinations.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": 50000
            }
        },
        "category": category,
        "price_tier": price_tier
    },
    {"_id": 1, "location": 1, "name": 1, "category": 1, "price_tier": 1}
    ).limit(limit)

    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return destinations


# When client clicks READ MORE about destination, log destination in Redis RAM to incr and track destination popularity
@router.post("/{destination_id}/visit", status_code=201)
def log_destination_visit(destination_id: str):
    db.redis_client.zincrby("trending_destinations", 1, destination_id)
    db.redis_client.delete("trending:top:10")
    return {"status": "visit logged", "destination_id": destination_id}
