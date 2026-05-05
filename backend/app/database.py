import os
import redis
from pymongo import MongoClient
from neo4j import GraphDatabase

class Database:
    """"State object to hold live connections"""
    mongo_client = None
    mongo_db = None
    neo4j_driver = None
    redis_client = None

db = Database()

def connect_databases():
    """Initialize connections."""
    print("Initializing database connection pools...")

    # =========  MongoDB  =========
    try:
        db.mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))        
        db.mongo_db = db.mongo_client["travel_db"]  # Create DB if not exists
        db.mongo_client.admin.command('ping')  # Verify connectivity

        # Indexing
        db.mongo_db.destinations.drop_indexes()
        db.mongo_db.destinations.create_index([("location", "2dsphere"), ("category", 1), ("price_tier", 1)])
        print("Successful connection to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    # =========  Neo4j  =========
    try:
        db.neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))  # Local Development
        )
        db.neo4j_driver.verify_connectivity()
        print("Successful connection to Neo4j.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")

    # =========  Redis  =========
    try:
        db.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        db.redis_client.ping()
        print("Successful connection to Redis.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")


def close_databases():
    """Close database connections."""
    print("Shut down: Closing database connections...")
    if db.mongo_client:
        db.mongo_client.close()
    if db.neo4j_driver:
        db.neo4j_driver.close()
    if db.redis_client:
        db.redis_client.close()
