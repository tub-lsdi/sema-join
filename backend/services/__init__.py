import duckdb

from .SemanticJoinService import SemanticJoinService
from .AIRecommendationService import AIRecommendationService
from .AppDatabaseService import AppDatabaseService
from .PMIService import PMIService
from backend.config import settings
from backend.utils import (
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
)


def get_db_connection(
    db_path: str = None, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the corpus DuckDB database.

    Args:
        db_path: Optional custom database path. If None, uses default location.
        read_only: Whether to open in read-only mode.

    Returns:
        DuckDB connection
    """
    db_to_use = db_path if db_path is not None else settings.DEFAULT_DB_PATH

    return duckdb.connect(
        database=db_to_use,
        config=settings.DEFAULT_DB_CONFIG,
        read_only=read_only,
    )


__all__ = [
    "SemanticJoinService",
    "AIRecommendationService",
    "AppDatabaseService",
    "PMIService",
    "NormalizationStrategy",
    "get_db_connection",
    "normalize_value",
    "set_normalization_strategy",
]
