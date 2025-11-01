"""
Services layer for semantic join API.
"""
import os
import duckdb
from dotenv import load_dotenv
from loguru import logger

from .SemanticJoinService import SemanticJoinService
from backend.utils import (
    NormalizationStrategy,
    normalize_value,
    set_normalization_strategy,
    extract_rows,
    stream_json_tables,
    table_hash,
)

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_DOTENV_PATH = os.path.join(_PROJECT_ROOT, ".env")
load_dotenv(_DOTENV_PATH)

_DB_EXTRA_PATH = os.getenv("DB_PATH", "corpus.db")
DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, _DB_EXTRA_PATH)

DEFAULT_DB_CONFIG = {}
_TEMP_DIR = os.getenv("DUCKDB_TEMP_DIRECTORY")
_MEM_LIMIT = os.getenv("DUCKDB_MEMORY_LIMIT")

if _TEMP_DIR:
    os.makedirs(_TEMP_DIR, exist_ok=True) # Ensure temp dir exists
    DEFAULT_DB_CONFIG['temp_directory'] = _TEMP_DIR

if _MEM_LIMIT:
    DEFAULT_DB_CONFIG['memory_limit'] = _MEM_LIMIT

# Log this one-time configuration load
if DEFAULT_DB_CONFIG:
    logger.debug("Default DuckDB config loaded from .env:")
    for key, value in DEFAULT_DB_CONFIG.items():
        logger.debug(f"  {key} = '{value}'")
logger.debug(f"Default DuckDB path set to: {DEFAULT_DB_PATH}")


# Utility function for database connection (used by setup scripts)
def get_db_connection(db_path: str = None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the DuckDB database.
    
    Args:
        db_path: Optional custom database path. If None, uses default location.
        
    Returns:
        DuckDB connection
    """
    db_to_use = db_path if db_path is not None else DEFAULT_DB_PATH

    return duckdb.connect(
        database=db_to_use,
        config=DEFAULT_DB_CONFIG,
        read_only=read_only,
    )


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
