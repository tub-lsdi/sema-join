
import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.services import SemanticJoinService
from backend.routes import health_router, bridge_router, join_router, ai_match_router


def get_db_path():
    """Get the database path from `.env` (DB_NAME)."""
    db_path = settings.DEFAULT_DB_PATH
    return db_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI app."""
    # Startup: create database connection
    db_path = get_db_path()
    app.state.db_connection = duckdb.connect(database=db_path)

    # Initialize the service with the connection
    app.state.join_service = SemanticJoinService(app.state.db_connection)

    yield

    # Shutdown: close database connection
    if hasattr(app.state, 'db_connection'):
        app.state.db_connection.close()


# Initialize FastAPI app
app = FastAPI(
    title="Semantic Join API",
    description="API for performing semantic joins on two lists of strings",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(bridge_router)
app.include_router(join_router)
app.include_router(ai_match_router)
