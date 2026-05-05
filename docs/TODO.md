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
* [ ] **Joseph:** Develop Redis Seed logic.
  * Inject initial ZSET data for `trending_destinations` so the frontend isn't blank on first boot.
* [x] **Together:** Write and execute `seed.py` inside the Docker container to populate all three databases simultaneously. **CRITICAL: Destination IDs must match perfectly across Mongo and Neo4j.**

## Phase 3: DB Indexing & Core Query Logic

**Goal:** Implement highly optimized queries utilizing database-specific strengths.

### MongoDB Sub-Tasks

* [x] **Create Compound & Geospatial Indexes:**
  * `db.destinations.createIndex({ "location": "2dsphere", "category": 1, "price_tier": 1 })`
* [ ] **Write Aggregation Pipeline 1 (`$geoNear`):**
  * Replace the `.find()` map query with a `$geoNear` pipeline that strictly projects `_id`, `name`, `location`, and a calculated `distance_in_meters`.
* [ ] **Write Aggregation Pipeline 2 (Inventory Analytics):**
  * Write a pipeline using `$match` (active status), `$group` (by category/price), and `$sort` to analyze platform inventory.

### Neo4j Sub-Tasks

* [ ] **Create Neo4j Indexes:**
  * `CREATE INDEX dest_id FOR (d:Destination) ON (d.id);`
  * `CREATE INDEX user_id FOR (u:User) ON (u.id);`
* [x] **Write Cypher Collaborative Filtering Query (Fixed-Length):**
  * Find destinations visited by "Travel Twins" (similar users). Must include sentiment weighting: `WHERE v.rating >= 4`.
* [ ] **Write Bounded Social Traversal Query (Variable-Length):**
  * Write a safe path traversal: `MATCH path = (u)-[:FRIENDS_WITH*1..2]-(network)-[v:VISITED]->(d)`. Must include rating filter and a strict `LIMIT 5` to prevent Supernode memory crashes.

### Redis Sub-Tasks

* [x] **Implement ZSET Logic for Trends:**
  * Write the logic to increment destination views: `ZINCRBY trending_destinations 1 {destination_id}`.
* [x] **Implement Read-Through Caching:**
  * Write the logic to cache the heavy top-10 trending calculations: `SET trending:top:10 "{json_payload}" EX 3600`. (DO NOT cache the GPS-dependent `/dashboard` orchestrator).

## Phase 4: Backend API Development

**Goal:** Expose the database queries via RESTful endpoints in the `routers/` directory.

* [ ] Build MongoDB Endpoints (`routers/destinations.py`).
  * [ ] `GET /destinations/near` (Triggers Pipeline 1: `$geoNear`).
  * [ ] `GET /analytics/inventory` (Triggers Pipeline 2: `$group` analytics).
* [ ] Build Neo4j Endpoints (`routers/dashboard.py`).
  * [x] `GET /dashboard/{user_id}` (The Orchestrator: Merges Collab Filtering, Redis Trending, and Mongo nearby pins into one JSON payload).
  * [ ] `GET /dashboard/{user_id}/social` (Triggers the bounded path traversal query).
* [x] Build Redis Endpoints (`routers/trending.py`).
  * [x] `GET /trending` (Triggers `ZREVRANGE` or fetches from cache).
  * [x] `POST /destinations/{destination_id}/visit` (Logs clicks to ZSET and invalidates `trending:top:10` cache).

## Phase 5: Streamlit Frontend Integration

**Goal:** Build the UI based on the professor's advice.

* [ ] Frontend Build
  * Build the Main Dashboard layout in `app.py`.
  * Set up the sidebar for user simulation.
  * Display the Neo4j recommendations and the social traversal network paths.
* [ ] Integrate Map Visualizations.
  * Use Streamlit's Mapbox integrations (`st.map` or `pydeck`) to plot the GeoJSON coordinates.

## Phase 6: Testing, Optimization, & Presentation Prep

**Goal:** Ensure everything runs fast and prepare to defend your architectural choices.

* [ ] **Irina:** Run `.explain("executionStats")` on Mongo pipelines to prove the partial indexes are working.
* [ ] **Sultan:** Run `PROFILE` on Cypher queries to prove the `*1..2` boundary prevents `AllNodesScan`s.
* [ ] **Joseph:** Verify the Cache Invalidation works using the Redis CLI `TTL trending:top:10` command (ensure it deletes and resets when a destination is visited).
* [ ] **Together:** Finalize the presentation, defending the polyglot persistence architecture and detailing the specific native-driver implementations used.
