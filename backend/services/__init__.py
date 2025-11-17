import duckdb

from .SemanticJoinService import SemanticJoinService
from .AIRecommendationService import AIRecommendationService
from .AppDatabaseService import AppDatabaseService
from backend.config import settings
from backend.utils import (
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
    extract_rows,
    stream_json_tables,
    table_hash,
)


# Utility function for database connection (used by setup scripts)
def get_db_connection(
    db_path: str = None, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the DuckDB database.

    Args:
        db_path: Optional custom database path. If None, uses default location.

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
    # Services
    "SemanticJoinService",
    "AIRecommendationService",
    "AppDatabaseService",
    # Utility functions
    "NormalizationStrategy",
    "get_db_connection",
    "normalize_value",
    "set_normalization_strategy",
    "extract_rows",
    "stream_json_tables",
    "table_hash",
]
