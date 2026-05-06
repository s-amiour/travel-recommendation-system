import os
import json
import random
import redis
from pymongo import MongoClient
from neo4j import GraphDatabase
from bson import ObjectId

########  Load/generate data   ########

def load_destinations_from_file(filepath="destinations.json"):
    print("Loading destinations from JSON...")
    
    with open(filepath, "r") as file:
        destinations = json.load(file)  # list of 50 destination objects
        
    # iterate parsed list and overwrite "_id"
    for dest in destinations:
        dest["_id"] = ObjectId()
        
    return destinations


def generate_users(count=20):
    # using simple string IDs for users to keep graph traversal fast
    return [{"id": f"u{i}", "name": f"User {i}"} for i in range(1, count + 1)]


########  Seed   ########


def seed_mongodb(mongo_db, destinations):
    print("Seeding MongoDB...")
    mongo_db.destinations.drop()
    mongo_db.destinations.insert_many(destinations)
    print(f" -> Inserted {len(destinations)} BSON documents.")


def seed_neo4j(neo4j_session, destinations, users):
    print("Seeding Neo4j...")
    neo4j_session.run("MATCH (n) DETACH DELETE n")  # wipe old graph

    # Create indexes to avoid full-table scans in dashboard queries
    neo4j_session.run("CREATE INDEX dest_id IF NOT EXISTS FOR (d:Destination) ON (d.id)")
    neo4j_session.run("CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)")
    
    # 1. create destination nodes (CRITICAL: Stringify the BSON ObjectId)
    for dest in destinations:
        neo4j_session.run(
            "CREATE (d:Destination {id: $id, name: $name, category: $category})",
            id=str(dest["_id"]), name=dest["name"], category=dest["category"]
        )
        
    # 2. create user nodes
    for user in users:
        neo4j_session.run(
            "CREATE (u:User {id: $id, name: $name})", 
            id=user["id"], name=user["name"]
        )
        
    # 3. create [:FRIENDS_WITH] social network
    print(" -> Building randomized social network...")
    for user in users:
        # give each user 1 to 4 random friends
        friends = random.sample(users, k=random.randint(1, 4)) 
        total_friendships += len(friends)
        for friend in friends:
            if user["id"] != friend["id"]:
                neo4j_session.run(
                    "MATCH (u:User {id: $u_id}), (f:User {id: $f_id}) "
                    "MERGE (u)-[:FRIENDS_WITH]-(f)",
                    u_id=user["id"], f_id=friend["id"]
                )  # the queries are separated by quotes as they are two statements
    # just a log of average no. of friends for each user
    print(f" -> Each user has, on average, {total_friendships / len(users)} friends") if len(users) > 0 else print("No users found.")

    # 4. create [:VISITED {rating}] interactions
    print(" -> Logging trips and sentiment ratings...")
    for user in users:
        # give each user 3 to 8 random trips
        visited_dests = random.sample(destinations, k=random.randint(3, 8)) 
        for dest in visited_dests:
            rating = random.randint(1, 5) # Assign a 1-5 star rating
            neo4j_session.run(
                "MATCH (u:User {id: $u_id}), (d:Destination {id: $d_id}) "
                "CREATE (u)-[:VISITED {rating: $rating}]->(d)",
                u_id=user["id"], d_id=str(dest["_id"]), rating=rating
            )

# Redis Seed

def seed_redis(redis_client, destinations):
    print("Seeding Redis...")
    redis_client.flushdb()  # Wipe old cache
    
    # assign baseline scores for each destination
    for dest in destinations:
        initial_score = random.randint(0, 100)
        redis_client.zadd("trending_destinations", {str(dest["_id"]): initial_score})

    print(" -> Trending ZSET baseline established.")

########  Executor   ########


def main():
    print("Starting Polyglot Database Seeding Pipeline...")
    
    # Connect to Drivers via environment variables (Docker-friendly)
    mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))
    )
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
)
    # Redis driver


    mongo_db = mongo_client["travel_db"]
    
    try:
        # 2. load Data & Generate Master Sync IDs in RAM
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        JSON_PATH = os.path.join(BASE_DIR, "destinations.json")
        destinations = load_destinations_from_file(JSON_PATH)
        users = generate_users(20)
        
        # 2. push Data to MongoDB (Document Storage)
        seed_mongodb(mongo_db, destinations)
        
        # 3. push Data to Neo4j (Graph Storage)
        with neo4j_driver.session() as session:
            seed_neo4j(session, destinations, users)
            
        # 4. push Data to Redis (Cache Storage)
        seed_redis(redis_client, destinations)
        
        
        print("\nSeeding Complete. All Database IDs are strictly synchronized.")
        
    except Exception as e:
        print(f"\nSeeding failed: {e}")
    finally:
        # Gracefully server connections to avoid crash
        mongo_client.close()
        neo4j_driver.close()
        redis_client.close()


if __name__ == "__main__":
    main()
