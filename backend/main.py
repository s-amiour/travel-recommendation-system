import os
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import MongoClient
from neo4j import GraphDatabase

# Global variables to hold our database connection pools
mongo_client = None
mongo_db = None
neo4j_driver = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, mongo_db, neo4j_driver, redis_client

    print("Initializing database connection pools...")

    # =========  MongoDB Connection  =========
    # Grab URI from Docker Compose, defaults to localhost for testing outside Docker
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    try:
        mongo_client = MongoClient(mongo_uri)
        # This will create the DB automatically if it doesn't exist
        mongo_db = mongo_client["travel_db"]
        mongo_client.admin.command('ping')  # Test the connection
        print("Successful connection to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    # =========  Neo4j Connection  =========
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
    try:
        neo4j_driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password))
        neo4j_driver.verify_connectivity()  # Test the connection
        print("Successful connection to Neo4j.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")

    # =========  Redis Connection  =========
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        redis_client.ping()
        print("Successful connection to Redis.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")

    # == Setup Done. Now, `yield` is hit, API starts accepting requests ==
    yield
    # == `lifespan` is called for the second time: meaning Shutdown Phase ==

    # Cleanup resources
    print("Shut down: Closing database connections...")
    if mongo_client:
        mongo_client.close()
    if neo4j_driver:
        neo4j_driver.close()
    if redis_client:
        redis_client.close()

# Initialize the FastAPI app with our connection pools
app = FastAPI(title="Travel Recommendation API", lifespan=lifespan)

# Test route


@app.get("/")
def read_root():
    return {"status": "API is healthy.", "databases": ["mongodb", "neo4j", "redis"]}

# Endpoint


@app.get("/destinations/near")
def get_nearby(lat: float, lng: float):
    results = mongo_db.destinations.find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": 5000
            }
        }
    })

    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return destinations


@app.post("/destinations/{destination_id}/visit")
def log_destination_visit(destination_id: str):
    redis_client.zincrby("trending_destinations", 1, destination_id)

    return {
        "status": "visit logged",
        "destination_id": destination_id
    }


@app.get("/trending")
def get_trending_destinations(limit: int = 10):
    trending = redis_client.zrevrange(
        "trending_destinations",
        0,
        limit - 1,
        withscores=True
    )

    return [
        {
            "destination_id": destination_id,
            "score": score
        }
        for destination_id, score in trending
    ]


@app.on_event("startup")
def create_index():
    mongo_db.destinations.create_index([("location", "2dsphere")])
