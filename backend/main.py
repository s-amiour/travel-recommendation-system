import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import MongoClient
from neo4j import GraphDatabase

# Global variables to hold our database connection pools
mongo_client = None
mongo_db = None
neo4j_driver = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, mongo_db, neo4j_driver

    print("Initializing database connection pools...")

    # =========  MongoDB Connection  =========
    # Grab URI from Docker Compose, defaults to localhost for testing outside Docker
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    try:
        mongo_client = MongoClient(mongo_uri)
        # This will create the DB automatically if it doesn't exist
        mongo_db = mongo_client["travel_db"]
        mongo_client.admin.command('ping')  # Test the connection
        mongo_db.destinations.create_index([("location", "2dsphere")])
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

    # placeholder for joseph's redis-py

    # == Setup Done. Now, `yield` is hit, API starts accepting requests ==
    yield
    # == `lifespan` is called for the second time: meaning Shutdown Phase ==

    # Cleanup resources
    print("Shut down: Closing database connections...")
    if mongo_client:
        mongo_client.close()
    if neo4j_driver:
        neo4j_driver.close()

# Initialize the FastAPI app with our connection pools
app = FastAPI(title="Travel Recommendation API", lifespan=lifespan)

# Test route


@app.get("/")
def read_root():
    return {"status": "API is healthy.", "databases": ["mongodb", "neo4j"]}

# Endpoint


@app.get("/destinations/near")
def get_nearby(lat: float, lng: float, radius: int = 5000, limit: int = 10):
    results = mongo_db.destinations.find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius
            }
        }
    }).limit(limit)

    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return destinations


@app.get("/destinations/search")
def search_destinations(
    country: str = None,
    category: str = None,
    min_rating: float = None,
    skip: int = 0,
    limit: int = 10
):
    pipeline = []
    match_filter = {}

    # filter by country if provided
    if country:
        match_filter["country"] = country

    if category:
        match_filter["category"] = category

    if min_rating is not None:
        match_filter["rating"] = {"$gte": min_rating}

    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.append({"$sort": {"rating": -1, "name": 1}})
    pipeline.append({"$skip": skip})
    pipeline.append({"$limit": limit})

    results = mongo_db.destinations.aggregate(pipeline)

    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return destinations


@app.get("/destinations/advanced-search")
def advanced_search(
    lat: float,
    lng: float,
    country: str = None,
    category: str = None,
    min_rating: float = None,
    radius: int = 5000,
    limit: int = 10
):
    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "distanceField": "distance",
                "maxDistance": radius,
                "spherical": True
            }
        }
    ]

    match_filter = {}

    if country:
        match_filter["country"] = country

    if category:
        match_filter["category"] = category

    if min_rating is not None:
        match_filter["rating"] = {"$gte": min_rating}

    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.append({"$sort": {"distance": 1}})
    pipeline.append({"$limit": limit})

    results = mongo_db.destinations.aggregate(pipeline)

    destinations = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        destinations.append(doc)

    return destinations
