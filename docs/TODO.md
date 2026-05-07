# Product Backlog: Phase Implementation

**Group 8 Team:**

* **Irina:** MongoDB (Native Driver), Geo-spatial Queries, Aggregation Pipelines.
* **Joseph:** Redis (`redis-py`), Caching Strategies (TTL/ZSET), API Orchestration.
* **Sultan:** Neo4j, Collaborative Filtering, Path Traversal, Streamlit Frontend, Docker.

**Tech Stack:** Python (FastAPI + Streamlit), MongoDB (Native Driver), Neo4j, Redis, Docker.
**Constraint:** No ODMs/ORMs (No Mongoose, MongoEngine, or py2neo). Direct native drivers ONLY.

---

## Phase 1: Environment & Infrastructure Setup

**Goal:** Establish containerized environment and verify connections.

* [x] **Sultan:** Create the `docker-compose.yml` file.
  * Provision 4 services: `mongodb`, `neo4j`, `redis`, and `backend` (FastAPI).
  * Ensure data persistence by mapping volumes for MongoDB (`/data/db`), Neo4j (`/data`), and Redis.
  * Create the initial `app.py` Streamlit file and verify it can hit the FastAPI backend set up by Irina.
* [x] **Irina:** Initialize Python Backend skeleton & Core DB Pools.
  * Set up the FastAPI app.
  * Establish connection pools using `pymongo` (MongoDB) and the `neo4j` native driver.
* [x] **Joseph:** Initialize Redis Pool.
  * Establish the `redis-py` connection pool in the backend.
* [x] **Together:** Boot the environment (`docker-compose up -d`) and test basic ping connections to all three databases.

## Phase 2: Data Modeling & The Seed Script

**Goal:** Populate the databases with reliable, realistic mock data to test complex queries.

* [x] **Irina:** Develop MongoDB Destination schemas and Seed logic.
  * Construct BSON documents for 50+ destinations including fields: `name`, `description`, `category`, `price_tier`, `status` (active/closed), and `location` (GeoJSON `Point`).
* [x] **Sultan:** Develop Neo4j Graph schema and Seed logic.
  * Define nodes: `(User)`, `(Destination)`.
  * Define relationships: `[:VISITED {rating: Integer}]` AND `[:FRIENDS_WITH]`.
* [x] **Joseph:** Develop Redis Seed logic.
  * Inject initial ZSET data for `trending_destinations` so the frontend isn't blank on first boot.
* [x] **Together:** Write and execute `seed.py` inside the Docker container to populate all three databases simultaneously. **CRITICAL: Destination IDs must match perfectly across Mongo and Neo4j.**

## Phase 3: DB Indexing & Hardening

**Goal:** The system works, but these steps prevent it from crashing or returning empty data during the demo.

### MongoDB Sub-Tasks

* [x] **Create Compound & Geospatial Indexes:**
  * `db.destinations.createIndex({ "location": "2dsphere", "category": 1, "price_tier": 1 })`
* [x] **Refactor `/near` for UI Distances:** Upgrade the `db.mongo_db.destinations.find()` query to an `aggregate([{ "$geoNear": ... }])` pipeline so the UI can display exact "Distance in Meters" to the user.

### Neo4j Sub-Tasks

* [x] **Create Production Indexes (Critical):** Run these in Neo4j browser or add to `seed.py` so the dashboard doesn't perform full-table scans:
  * `CREATE INDEX dest_id IF NOT EXISTS FOR (d:Destination) ON (d.id);`
  * `CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id);`
* [x] **Write Cypher Collaborative Filtering Query (Fixed-Length):**
  * Find destinations visited by "Travel Twins" (similar users). Must include sentiment weighting: `WHERE v.rating >= 4`.
* [x] **Upgrade the Recommendation Engine:** Replace the 1-hop query in `dashboard.py` with the Variable-Length Bounded Traversal to prevent "Ghost Town" empty results for users with few friends.

```cypher
MATCH (u:User {id: $user_id})-[:FRIENDS_WITH*1..2]-(network_user)
WHERE u <> network_user 
WITH DISTINCT network_user
MATCH (network_user)-[v:VISITED]->(d:Destination)
WHERE v.rating >= 4
RETURN d.id AS destination_id, COUNT(network_user) AS score
ORDER BY score DESC LIMIT 10
```

### Redis Sub-Tasks

* [x] **Implement ZSET Logic for Trends:**
  * Write the logic to increment destination views: `ZINCRBY trending_destinations 1 {destination_id}`.
* [x] **Implement Read-Through Caching:**
  * Write the logic to cache the heavy top-10 trending calculations: `SET trending:top:10 "{json_payload}" EX 3600`. (DO NOT cache the GPS-dependent `/dashboard` orchestrator).
* [x] **Doc Update:** Rename "Read-Through" to "Cache-Aside" in docstring for accuracy.

## Phase 4: Streamlit Frontend Integration

**Goal:** Currently, `app.py` just pings the backend. We need to wire it up to the polyglot endpoints.

* [ ] **User & Location Context UI:** Add Streamlit `st.selectbox` to let the tester pick one of the 20 bot `user_id`s.
  * Add input fields (or a map/dropdown of preset cities) to capture `lat` and `lng`.
* [ ] **Consume the Dashboard Endpoint:**
  * Trigger `GET /dashboard/{user_id}?lat={lat}&lng={lng}` when the user submits their context.
* [ ] **Render the 3 Data Tiers:**
  * Create UI section for "Network Recommendations" (Iterate over `response["recommendations"]`).
  * Create UI section for "Trending Globally" (Iterate over `response["trending"]`). Display the `trending_score`.
  * Create UI section for "Nearby Discoveries" (Iterate over `response["nearby"]`).
* [ ] **Wire the "Visit/Read More" Trigger:**
  * Add a Streamlit `st.button` under each destination card.
  * When clicked, fire `POST` request to `/destinations/{destination_id}/visit` to increment Redis score and trigger cache invalidation.

## Phase 5: Beta Polish

**Goal:** Ensure everything runs fast and prepare to defend your architectural choices.

* [ ] **Verify Seed Data Accuracy:** Ensure MongoDB `_ids`, Neo4j `id`s, and Redis `destination_ids` perfectly match across the databases so the "hydration" step in the dashboard doesn't return empty JSON objects.
* [ ] **Test the Cache Reset:** Click "Read More" button on a destination, refresh the Streamlit page, and visually verify its score went up in the "Trending Globally" section.
* [ ] **Clean Docker Logs:** Run `docker-compose up --build` and ensure no `500 Internal Server Error` or `Connection Refused` traces appear during cold boot.
