from fastapi import APIRouter
from bson import ObjectId
from app.database import db
from app.routers.trending import get_trending_destinations

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{user_id}")
def get_dashboard(user_id: str, lat: float, lng: float):
    # 1. Extract results of recommendation logic to a list
    rec_query = """
    MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]-(friend:User)-[v:VISITED]->(rec:Destination)
    WHERE v.rating >= 4 AND NOT (u)-[:VISITED]->(rec)
    RETURN rec.id AS destination_id, count(*) AS score
    ORDER BY score DESC LIMIT 10
    """
    with db.neo4j_driver.session() as session:
        rec_results = session.run(rec_query, user_id=user_id)
        raw_recommendations = [{"destination_id": r["destination_id"], "score": r["score"]} for r in rec_results]

    # 2. Extract top five trending destinations based on score
    cached_trending_payload = get_trending_destinations()  # we keep it as default to conform to trending:top:10 standard cache
    raw_trending = cached_trending_payload[:5]

    # ======  3. Fetch BOTH trending and recommended complete destination objects ======
    # i.e. HYDRATING neo4j and redis objects

    neo4j_ids = [r["destination_id"] for r in raw_recommendations]
    redis_ids = [r["destination_id"] for r in raw_trending]
    
    unique_ids_str = list(set(neo4j_ids + redis_ids))
    object_ids_to_fetch = [ObjectId(id_str) for id_str in unique_ids_str]

    rich_data_cursor = db.mongo_db.destinations.find({"_id": {"$in": object_ids_to_fetch}})
    
    # build O(1) lookup table (hash map) in python memory
    rich_data_map = {}
    for doc in rich_data_cursor:
        doc["_id"] = str(doc["_id"]) # cast back to string for JSON serialization
        rich_data_map[doc["_id"]] = doc

    # 4. Assembling score property to destinations
    final_recommendations = []
    for rec in raw_recommendations:
        dest_id = rec["destination_id"]
        if dest_id in rich_data_map:
            full_dest = rich_data_map[dest_id].copy()
            full_dest["social_score"] = rec["score"]
            final_recommendations.append(full_dest)

    final_trending = []
    for trend in raw_trending:
        dest_id = trend["destination_id"]
        if dest_id in rich_data_map:
            full_dest = rich_data_map[dest_id].copy()
            full_dest["trending_score"] = trend["score"]
            final_trending.append(full_dest)

    # 5. Proximity (geospatial) query
    nearby_cursor = db.mongo_db.destinations.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": 50000
            }
        }
    }, {"_id": 1, "location": 1, "name": 1, "category": 1}).limit(5)
    
    final_nearby = []
    for doc in nearby_cursor:
        doc["_id"] = str(doc["_id"])
        final_nearby.append(doc)

    # Backend-For-Frontend architectural pattern
    return {
        "recommendations": final_recommendations, 
        "trending": final_trending, 
        "nearby": final_nearby
    }