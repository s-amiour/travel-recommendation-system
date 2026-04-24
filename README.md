# Travel Recommendation System

This project is a polyglot persistence project designed to recommend next destination suggestions based on a client’s travel history, geographic location, and personal preferences. By leveraging the unique strengths of three distinct database systems, this project delivers real-time, location-aware, and highly personalized travel recommendations.

## Architecture Overview

The architecture of the project will utilise microservices orchestrated via Docker:

* **Frontend:** [Streamlit](https://streamlit.io/) – For interactive maps, trend dashboards, and a simulated user interface.
* **Backend:** Python (FastAPI / Flask) – Serves as the API orchestrator and aggregator.
* **Location & Metadata Hub:** **MongoDB** (Native Driver)
  * Stores destination details and GeoJSON coordinates.
  * Utilizes `2dsphere` spatial indexing for lightning-fast `$near` queries.
  * Employs partial and covering indexes for optimized aggregation pipelines.
* **Recommendation Engine:** **Neo4j**
  * A graph database mapping `(User)`, `(Destination)`, and `(Category)` nodes.
  * Executes Collaborative Filtering via Cypher queries to find destinations based on shared preferences and travel histories.
* **Popular Trends Cache:** **Redis**
  * Uses Sorted Sets (ZSET) to track destination popularity in real-time.
  * Implements a 1-hour TTL dashboard cache to optimize heavy query execution.
* **Infrastructure:** Docker & Docker Compose

## Features to be Implemented

1. **Geolocation Search:** Instantly find destinations within a specific radius of the user's current coordinates.
2. **Personalized Graph Recommendations:** Suggests unvisited destinations matching user preferences, ranked higher if similar users have visited them.
3. **Real-Time Trending Board:** A constantly updated list of trending destinations based on user views and visits.
4. **Optimized Caching:** Aggregated dashboard results are cached in Redis to minimize database load.

## Setup to be Implemented

### Pre-requisites

* [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
* Python 3.9+

### Installation

1. **Clone repository**

```bash
git clone [https://github.com/s-amiour/travel-recommendation-system.git](https://github.com/s-amiour/travel-recommendation-system.git)
cd travel-recommendation-system
```

2. **Spin up the Database Environment**

Launch MongoDB, Neo4j, Redis, and the Backend API containers.

```bash
docker-compose up -d
```

3. **Run the Seed Script**
Populate the databases with mock users, active destinations, relationship graphs, and initial trends.

```bash
docker exec -it backend-container python seed.py
```

4. **Access the Application**

* **Frontend (Streamlit):** `http://localhost:8501`
* **Backend API Docs:** `http://localhost:8000/docs`
* **Neo4j Browser:** `http://localhost:7474`

## API Endpoints (To Be Implemented)

* `GET /destinations/near` - Find nearby destinations using MongoDB spatial queries.
* `GET /users/{id}/recommendations` - Get personalized collaborative filtering recommendations from Neo4j.
* `GET /trending` - Retrieve top 10 trending destinations from Redis.
* `POST /users/{id}/visit` - Log a visit (updates Neo4j graph and increments Redis ZSET).
* `GET /dashboard/{user_id}` - Aggregated endpoint leveraging Redis cache for the Streamlit UI.

## Tech Stack

* Frontend: Python (Streamlit)
* Backend: Python, MongoDB, Neo4j, Redis, Docker

## Team

* **Irina:** MongoDB (Native Driver), Geo-spatial Queries, Aggregation Pipelines.
* **Joseph:** Redis (`redis-py`), Caching Strategies (TTL/ZSET), API Orchestration.
* **Sultan:** Neo4j, Collaborative Filtering, Path Traversal, Streamlit Frontend, Docker.
