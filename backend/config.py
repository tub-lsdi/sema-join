import sys
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import computed_field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Project settings managed with Pydantic, which automatically reads from .env files.
    """

    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "backend" / "corpus" / "data"
    INPUT_DIR: Path = DATA_DIR

    # DuckDB settings
    DB_PATH: str = "corpus.db"
    DUCKDB_TEMP_DIRECTORY: Path = PROJECT_ROOT
    TEMP_META_DIR_NAME: Path = "temp_parquet_meta"
    TEMP_CELLS_DIR_NAME: Path = "temp_parquet_cells"
    DUCKDB_MEMORY_LIMIT: str = "10GB"

    LOG_LEVEL: str = "DEBUG"

    CELL_BATCH_SIZE: int = 1_000_000
    TABLE_BATCH_SIZE: int = 50_000

    # Ollama AI settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 60

    @property
    def DEFAULT_DB_PATH(self) -> Path:
        """Provides the absolute path to the database file."""
        # Use PROJECT_ROOT to build the full, absolute path
        return self.PROJECT_ROOT / self.DB_PATH

    @property
    def TEMP_META_DIR(self) -> Path:
        """Provides the absolute path to the temp metadata directory."""
        return self.DUCKDB_TEMP_DIRECTORY / self.TEMP_META_DIR_NAME

    @property
    def TEMP_CELLS_DIR(self) -> Path:
        """Provides the absolute path to the temp cells directory."""
        return self.DUCKDB_TEMP_DIRECTORY / self.TEMP_CELLS_DIR_NAME

    @property
    def DEFAULT_DB_PATH(self) -> Path:
        """Provides the absolute path to the database file."""
        # Use PROJECT_ROOT to build the full, absolute path
        return self.PROJECT_ROOT / self.DB_PATH

    @computed_field(return_type=dict[str, Any])
    @property
    def DEFAULT_DB_CONFIG(self) -> dict[str, Any]:
        """Generates the DuckDB config dict based on .env settings."""
        config = {}
        if self.DUCKDB_TEMP_DIRECTORY:
            # Pydantic already converted this to a Path,
            # but DuckDB needs a string.
            config["temp_directory"] = str(self.DUCKDB_TEMP_DIRECTORY)
        if self.DUCKDB_MEMORY_LIMIT:
            config["memory_limit"] = self.DUCKDB_MEMORY_LIMIT
        return config

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

try:
    if settings.DUCKDB_TEMP_DIRECTORY:
        settings.DUCKDB_TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)

    # Also ensure the other temp dirs exist
    settings.TEMP_META_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_CELLS_DIR.mkdir(parents=True, exist_ok=True)

except PermissionError as e:
    logger.error(f"Permission error creating temp directories: {e}")
except Exception as e:
    logger.error(f"Failed to create temp directories: {e}")


# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)

logger.debug("Configuration loaded successfully:")
logger.debug(f"  Default DuckDB path set to: {settings.DEFAULT_DB_PATH}")

if settings.DEFAULT_DB_CONFIG:
    logger.debug("  Default DuckDB config loaded from .env:")
    for key, value in settings.DEFAULT_DB_CONFIG.items():
        logger.debug(f"    {key} = '{value}'")
else:
    logger.debug("  No extra DuckDB config (temp_directory or memory_limit) found.")
