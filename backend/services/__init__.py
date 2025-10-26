"""
Services layer for semantic join API.
"""
import os
import duckdb

from .CorpusService import (
    CorpusService,
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
    extract_rows_from_wdc_dict,
    stream_json_tables,
    table_hash,
)
from .SemanticJoinService import SemanticJoinService


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
        # Calculate project root from backend/services/__init__.py
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        db_path = os.path.join(project_root, "db.py")
    
    return duckdb.connect(database=db_path)


__all__ = [
    # Services
    "CorpusService",
    "SemanticJoinService",
    "NormalizationStrategy",
    # Utility functions
    "get_db_connection",
    "normalize_value",
    "set_normalization_strategy",
    "extract_rows_from_wdc_dict",
    "stream_json_tables",
    "table_hash",
]
