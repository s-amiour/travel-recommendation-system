# Phase Implementation for Team

**Group 8 Team:** Irina (MongoDB, API, Geo-queries) & Sultan (Neo4j, Redis, Docker)

**Tech Stack:** Python (Backend + Streamlit Frontend), MongoDB (Native Driver), Neo4j, Redis, Docker.

---

## Phase 1: Environment & Infrastructure Setup

**Goal:** Establish containerized environment and verify connections.

* [ ] **Sultan:** Create the `docker-compose.yml` file.
  * Provision 4 services: `mongodb`, `neo4j`, `redis`, and `backend` (Python API).
  * Ensure data persistence by mapping volumes for MongoDB (`/data/db`), Neo4j (`/data`), and Redis.
  * Expose necessary ports (e.g., Mongo: `27017`, Neo4j: `7687`/`7474`, Redis: `6379`, Backend: `8000`).
* [ ] **Irina:** Initialize Python Backend skeleton.
  * Set up a FastAPI or Flask app. (we’ll discuss which one)
  * Establish connection pools using the `pymongo`(MongoDB native driver), `neo4jdriver`, and `redis-py` driver.
* [ ] **Together:** Boot the environment (`docker-compose up -d`) and test basic ping connections to all three databases from the backend container.

## Phase 2: Data Modeling & The Seed Script

**Goal:** Populate the databases with reliable, realistic mock data to test complex queries.

* [ ] **Irina:** Develop MongoDB Destination schemas and Seed logic.
  * Construct BSON documents for 50+ destinations including fields: `name`, `description`, `category`, `status` (active/inactive), and `location` (GeoJSON `Point`).
* [ ] **Sultan:** Develop Neo4j Graph schema and Seed logic.
  * Define nodes: `(User)`, `(Destination)`, `(Category)`.
  * Define relationships: `[:VISITED]`, `[:PREFERS]`, `[:BELONGS_TO]`.
* [ ] **Together:** Write and execute `seed.py`.
  * Connect to MongoDB and insert the 50 destinations.
  * Connect to Neo4j, create mock users, and map relationships linking to the same Destination IDs used in MongoDB.
  * Connect to Redis and inject some initial ZSET data for `popular_trends`.

## Phase 3: DB Indexing & Core Query Logic

**Goal:** Implement highly optimized queries. DB Expert Focus: Partial and Covering Indexes.

### MongoDB Sub-Tasks (Irina)

* [ ] **Create Geo-Spatial & Partial Indexes:**
  * Line-by-line explanation: We don't want to index draft or closed locations.
  * `db.destinations.createIndex({ "location": "2dsphere" }, { partialFilterExpression: { status: "active" } })` -> Partial Index: Only indexes active locations, saving RAM and improving write performance.
* [ ] **Create Covering Indexes for Aggregation:**
  * Per the professor's advice to use an Aggregation Pipeline (group by category/preference).
    * `db.destinations.createIndex({ category: 1, "metrics.preferenceScore": -1, name: 1, _id: 0 })` -> Covering Index: If the pipeline only projects category, score,and name, MongoDB reads directly from RAM without touching the disk collection.
* [ ] **Write Core Queries:**
  * Implement the native `$near` or `$geoWithin` query.
  * Implement the Aggregation Pipeline: `$match` active locations -> `$group` by category -> `$sort`.

### Neo4j & Redis Sub-Tasks (Sultan)

* [ ] **Create Neo4j Indexes:**
  * `CREATE INDEX dest_id FOR (d:Destination) ON (d.id);` -> Crucial for fast $O(\log N)$ lookups when bridging Mongo IDs to Neo4j Nodes.
* [ ] **Write Cypher Collaborative Filtering Query:**
  * Line-by-line interpretation:
    * `MATCH (u:User {id: $userId})-[:PREFERS]->(c:Category)<-[:BELONGS_TO]-(d:Destination)` -> Find destinations matching preferred categories.
    * `WHERE NOT (u)-[:VISITED]->(d)` -> Exclude already visited.
    * `OPTIONAL MATCH (other:User)-[:VISITED]->(d) WHERE other <> u` -> Collaborative filtering step.
    * `RETURN d.id, count(other) AS popularity ORDER BY popularity DESC` -> Rank them.
* [ ] **Implement Redis ZSET & TTL Caching:**
  * Professor's Advice: Dashboard Cache with 1-hour TTL.
  * Write logic to cache the combined homepage dashboard result: `SET dashboard:user:{id} "{json_payload}" EX 3600`.
  * Write logic to increment trends: `ZINCRBY trending_destinations 1 {destination_id}`.

## Phase 4: Backend API Development

**Goal:** Expose the database queries via RESTful endpoints.

* [ ] **Irina & Sultan:** Implement the required API endpoints.
  * `GET /destinations/near`: Triggers MongoDB `$near` query.
  * `GET /users/{id}/recommendations`: Triggers Neo4j Cypher query.
  * `GET /trending`: Triggers Redis `ZREVRANGE trending_destinations 0 9 WITHSCORES`.
  * `POST /users/{id}/visit`:
    * Async update: Adds `[:VISITED]` in Neo4j.
    * Async update: Triggers `ZINCRBY` in Redis.
* [ ] **Together:** Implement the Aggregator / Orchestrator Function.
  * When the frontend calls for the main dashboard, check Redis first (`GET dashboard:user:{id}`). If it misses, fetch Neo4j recommendations + Mongo Geo-locations, merge the JSON, return to client, and cache in Redis with the 1-hour TTL.

## Phase 5: Streamlit Frontend Integration (Day 6)

**Goal:** Build the UI based on the professor's advice.

* [ ] **Together:** Initialize `app.py` using Streamlit.
  * Create a sidebar for user authentication/selection (mocking a logged-in user).
  * Create a map visualization (using Streamlit's `st.map` or `folium` integration) plotting the coordinates returned from `GET /destinations/near`.
  * Display the "Trending Now" list from Redis at the top of the dashboard.
  * Display personalized recommendations (Neo4j results matched with MongoDB descriptive data).
  * Add a "Simulate Visit" button that triggers the `POST /users/{id}/visit` endpoint to demonstrate real-time Redis trend updates.

## Phase 6: Testing, Optimization, & Presentation Prep

**Goal:** Ensure everything runs fast and prepare to defend your architectural choices.

* [ ] **Irina:** Run `.explain("executionStats")` on the MongoDB queries.
  * Verify that `totalDocsExamined` is close to `nReturned`. If `totalDocsExamined` is way higher, the covering indexes are failing and need adjustment.
* [ ] **Sultan:** Run `PROFILE` before the Cypher query in Neo4j browser to ensure it hits the node index rather than doing an `AllNodesScan`.
* [ ] **Together:** Finalize the presentation.
  * Highlight the exact professor's advice implemented (1-hour TTL in Redis, Streamlit UI, Mongo Aggregation).
  * Explain the "Why": Why you separated spatial data (Mongo) from relational mapping (Neo4j) and fast counters/cache (Redis).
  * Highlight the use of Partial and Covering indexes as your primary method for hardware resource conservation.
