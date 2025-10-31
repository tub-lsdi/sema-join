"""
Services layer for semantic join API.
"""
import os
import duckdb
from dotenv import load_dotenv

from .SemanticJoinService import SemanticJoinService
from backend.utils import (
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
    extract_rows,
    stream_json_tables,
    table_hash,
)


# Utility function for database connection (used by setup scripts)
def get_db_connection(db_path: str = None) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the DuckDB database.
    
    Args:
        db_path: Optional custom database path. If None, uses default location.
        
    Returns:
        DuckDB connection
    """
    if db_path is None:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        dotenv_path = os.path.join(project_root, ".env")
        load_dotenv(dotenv_path)
        db_extra_path = os.getenv("DB_PATH", "corpus.db")
        db_path = os.path.join(project_root, db_extra_path)
    
    return duckdb.connect(database=db_path)


__all__ = [
    # Services
    "SemanticJoinService",
    # Utility functions
    "NormalizationStrategy",
    "get_db_connection",
    "normalize_value",
    "set_normalization_strategy",
    "extract_rows",
    "stream_json_tables",
    "table_hash",
]
