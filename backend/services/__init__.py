"""
Services layer for semantic join API.
"""
import os
import duckdb

from .SemanticJoinService import SemanticJoinService
from backend.utils import (
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
    extract_rows_from_wdc_dict,
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
        db_path = os.path.join(project_root, "db.py")
    
    return duckdb.connect(database=db_path)


__all__ = [
    # Services
    "SemanticJoinService",
    # Utility functions
    "NormalizationStrategy",
    "get_db_connection",
    "normalize_value",
    "set_normalization_strategy",
    "extract_rows_from_wdc_dict",
    "stream_json_tables",
    "table_hash",
]
