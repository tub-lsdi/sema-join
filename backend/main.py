"""
FastAPI backend for Semantic Join operations.
"""

import os
import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from backend.services import SemanticJoinService
from backend.routes import (
    health_router,
    bridge_router,
    join_router,
    history_router,
)
from backend.app_db import init_app_db, shutdown_app_db


def get_db_path():
    """Get the database path."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "corpus.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI app."""
    # Startup: create database connection
    db_path = get_db_path()
    app.state.db_connection = duckdb.connect(database=db_path)

    # Initialize the service with the connection
    app.state.join_service = SemanticJoinService(app.state.db_connection)

    # Initialize and attach the application MySQL DB (SQLAlchemy)
    init_app_db(app)

    yield

    # Shutdown: close database connection(s)
    if hasattr(app.state, "db_connection"):
        app.state.db_connection.close()
        shutdown_app_db(app)


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
app.include_router(history_router)
