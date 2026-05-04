from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import connect_databases, close_databases
from app.routers import destinations, trending, dashboard

# Ensure connections start when container boots up; cleanly close when container shuts down.
@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_databases()
    # == Setup Done. Now, `yield` is hit, API starts accepting requests ==
    yield
    # == `lifespan` is called for the second time: meaning Shutdown Phase ==
    close_databases()

# Initialize the FastAPI app with connection pools
app = FastAPI(title="Travel Recommendation API", lifespan=lifespan)

app.include_router(destinations.router)
app.include_router(trending.router)
app.include_router(dashboard.router)

@app.get("/", tags=["root"])
def read_root():
    return {"status": "API is healthy.", "databases": ["mongodb", "neo4j", "redis"]}
