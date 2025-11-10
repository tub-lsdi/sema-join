from .health import router as health_router
from .bridge import router as bridge_router
from .join import router as join_router
from .ai_match import router as ai_match_router
from .history import router as history_router

__all__ = [
    "health_router",
    "bridge_router",
    "join_router",
    "ai_match_router",
    "history_router",
]
