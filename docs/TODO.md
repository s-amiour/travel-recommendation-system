# Product Backlog: Phase Implementation

**Group 8 Team:**

* **Irina:** MongoDB (Native Driver), Geo-spatial Queries, Aggregation Pipelines.
* **Joseph:** Redis (`redis-py`), Caching Strategies (TTL/ZSET), Streamlit Frontend, API Orchestration.
* **Sultan:** Neo4j, Collaborative Filtering, Path Traversal, Docker.

**Tech Stack:** Python (FastAPI + Streamlit), MongoDB (Native Driver), Neo4j, Redis, Docker.
**Constraint:** No ODMs/ORMs (No Mongoose, MongoEngine, or py2neo). Direct native drivers ONLY.

---

## Phase 1: Environment & Infrastructure Setup

**Goal:** Establish containerized environment and verify connections.

* [ ] **Sultan:** Create the `docker-compose.yml` file.
  * Provision 4 services: `mongodb`, `neo4j`, `redis`, and `backend` (FastAPI).
  * Ensure data persistence by mapping volumes for MongoDB (`/data/db`), Neo4j (`/data`), and Redis.
* [ ] **Irina:** Initialize Python Backend skeleton & Core DB Pools.
  * Set up the FastAPI app.
  * Establish connection pools using `pymongo` (MongoDB) and the `neo4j` native driver.
* [ ] **Joseph:** Initialize Redis Pool & Frontend Skeleton.
  * Establish the `redis-py` connection pool in the backend.
  * Create the initial `app.py` Streamlit file and verify it can hit the FastAPI backend.
* [ ] **Together:** Boot the environment (`docker-compose up -d`) and test basic ping connections to all three databases.

## Phase 2: Data Modeling & The Seed Script

**Goal:** Populate the databases with reliable, realistic mock data to test complex queries.

* [ ] **Irina:** Develop MongoDB Destination schemas and Seed logic.
  * Construct BSON documents for 50+ destinations including fields: `name`, `description`, `category`, `status`, and `location` (GeoJSON `Point`).
    * Find seed data online by searching data given by github repos or APIs, etc.
* [ ] **Sultan:** Develop Neo4j Graph schema and Seed logic.
  * Define nodes: `(User)`, `(Destination)`, `(Category)`.
  * Define relationships: `[:VISITED]`, `[:PREFERS]`, `[:BELONGS_TO]`, and `[:FRIENDS_WITH]` (for path traversals).
* [ ] **Joseph:** Develop Redis Seed logic.
  * Inject initial ZSET data for `popular_trends` so the frontend isn't blank on first boot.
* [ ] **Together:** Write and execute `seed.py` to synchronize IDs across all three databases.

## Phase 3: DB Indexing & Core Query Logic

**Goal:** Implement highly optimized queries utilizing database-specific strengths.

### MongoDB Sub-Tasks (Irina)

* [ ] **Create Geo-Spatial & Partial Indexes:**
  * `db.destinations.createIndex({ "location": "2dsphere" }, { partialFilterExpression: { status: "active" } })` -> Only indexes active locations to save RAM.
* [ ] **Create Covering Indexes & Aggregation Pipeline:**
  * Define the index: `db.destinations.createIndex({ category: 1, "metrics.preferenceScore": -1, name: 1, _id: 0 })`.
  * Write the pipeline: Use `$match` (active locations) -> `$group` (by category) -> `$sort` (by score) to return grouped recommendations purely from the native driver.
    * Write an aggregation pipeline for each endpoint.

### Neo4j Sub-Tasks (Sultan)

* [ ] **Create Neo4j Indexes:**
  * `CREATE INDEX dest_id FOR (d:Destination) ON (d.id);` for fast $O(\log N)$ bridge lookups.
* [ ] **Write Cypher Collaborative Filtering & Path Traversal Queries:**
  * *Collab Filter:* Find destinations matching preferred categories that the user hasn't visited, ranked by how many other users visited them.
  * *Path Traversal:* Write a variable-length path query (e.g., `MATCH p=shortestPath((u:User {id: $id})-[:FRIENDS_WITH*1..3]-(other:User))-[:VISITED]->(d:Destination)`) to recommend places based on a "social network" traversal.

### Redis Sub-Tasks (Joseph)

* [ ] **Implement ZSET Logic for Trends:**
  * Write the logic to increment destination views: `ZINCRBY trending_destinations 1 {destination_id}`.
* [ ] **Implement TTL Dashboard Caching:**
  * Write the logic to cache the heavy orchestrator payload: `SET dashboard:user:{id} "{json_payload}" EX 3600`. (Professor's 1-hour TTL advice).

## Phase 4: Backend API Development

**Goal:** Expose the database queries via RESTful endpoints.

* [ ] **Irina:** Build MongoDB Endpoints.
  * `GET /destinations/near` (Triggers `$near` query).
  * `GET /destinations/grouped` (Triggers Aggregation Pipeline).
* [ ] **Sultan:** Build Neo4j Endpoints.
  * `GET /users/{id}/recommendations` (Triggers Collab Filter).
  * `GET /users/{id}/network-recs` (Triggers Path Traversal).
* [ ] **Joseph:** Build Redis Endpoints & The Orchestrator.
  * `GET /trending` (Triggers `ZREVRANGE`).
  * **The Orchestrator:** Build the `GET /dashboard/{id}` endpoint. Check Redis first. If cache miss -> fetch asynchronously from Irina's Mongo logic and Sultan's Neo4j logic -> merge JSON -> save to Redis -> return to client.

## Phase 5: Streamlit Frontend Integration

**Goal:** Build the UI based on the professor's advice.

* [ ] **Sultan:**
  * Build the Main Dashboard layout in `app.py`.
    * Set up the sidebar for user simulation.
    * Fetch and display the top-level Redis "Trending Now" dashboard.
  * Integrate Network/Recommendation Visualizations.
    * Display the Neo4j recommendations, clearly showing *why* a place was recommended (e.g., "Because 3 of your 2nd-degree connections visited this!").
* [ ] **Irina:** Integrate Map Visualizations.
  * Use Streamlit's `st.map` or `folium` to plot the GeoJSON coordinates fetched from MongoDB.

## Phase 6: Testing, Optimization, & Presentation Prep

**Goal:** Ensure everything runs fast and prepare to defend your architectural choices.

* [ ] **Irina:** Run `.explain("executionStats")` on Mongo queries to prove the partial/covering indexes are preventing full collection scans.
* [ ] **Sultan:** Run `PROFILE` on Cypher queries to ensure variable-length path traversals aren't causing Cartesian products or `AllNodesScan`s.
* [ ] **Joseph:**
  * Monitor Redis memory and
  * Verify the TTL expiration is working correctly using the Redis CLI `TTL dashboard:user:{id}` command.
  * Initialize presentation of project.
* [ ] **Together:** Finalize the presentation, defending the polyglot persistence architecture and detailing the specific native-driver implementations used.
