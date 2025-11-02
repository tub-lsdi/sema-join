"""
API routes for the Semantic Join backend.
"""

from .health import router as health_router
from .bridge import router as bridge_router
from .join import router as join_router
from .history import router as history_router

__all__ = ["health_router", "bridge_router", "join_router", "history_router"]
