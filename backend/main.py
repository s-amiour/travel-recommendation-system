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
        mongo_db = mongo_client["travel_db"]  # This will create the DB automatically if it doesn't exist
        mongo_client.admin.command('ping')  # Test the connection
        print("Successful connection to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    # =========  Neo4j Connection  =========
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
    try:
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
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