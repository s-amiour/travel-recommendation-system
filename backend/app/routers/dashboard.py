from fastapi import APIRouter
from database import db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{user_id}")
def get_dashboard(user_id: str, lat: float, lng: float):
    # Neo4j
    rec_query = """
    MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]-(friend:User)-[v:VISITED]->(rec:Destination)
    WHERE v.rating >= 4 AND NOT (u)-[:VISITED]->(rec)
    RETURN rec.id AS destination_id, count(*) AS score
    ORDER BY score DESC
    LIMIT 5
    """
    with db.neo4j_driver.session() as session:
        rec_results = session.run(rec_query, user_id=user_id)
        recommendations = [{"destination_id": r["destination_id"], "score": r["score"]} for r in rec_results]

    # Redis
    trending = db.redis_client.zrevrange("trending_destinations", 0, 4, withscores=True)
    trending_result = [{"destination_id": d, "score": s} for d, s in trending]

    # MongoDB
    nearby_cursor = db.mongo_db.destinations.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": 50000
            }
        }
    }, {"_id": 1, "location": 1, "name": 1}).limit(5)
    
    nearby = []
    for doc in nearby_cursor:
        doc["_id"] = str(doc["_id"])
        nearby.append(doc)

    return {"recommendations": recommendations, "trending": trending_result, "nearby": nearby}
