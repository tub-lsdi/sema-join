import sys
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import computed_field
from pydantic_settings import BaseSettings

# Root of the entire project (parent of corpus/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class CorpusSettings(BaseSettings):
    """Settings for corpus ingestion."""

    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "corpus" / "data"
    INPUT_DIR: Path = DATA_DIR

    # DuckDB settings - corpus.db stored at project root
    DB_PATH: str = "corpus.db"
    DUCKDB_TEMP_DIRECTORY: Path = PROJECT_ROOT
    TEMP_META_DIR_NAME: str = "temp_parquet_meta"
    TEMP_CELLS_DIR_NAME: str = "temp_parquet_cells"
    DUCKDB_MEMORY_LIMIT: str = "10GB"

    LOG_LEVEL: str = "INFO"

    CELL_BATCH_SIZE: int = 1_000_000
    TABLE_BATCH_SIZE: int = 50_000

    @property
    def DEFAULT_DB_PATH(self) -> Path:
        """Provides the absolute path to the corpus database file."""
        return self.PROJECT_ROOT / self.DB_PATH

    @property
    def TEMP_META_DIR(self) -> Path:
        """Provides the absolute path to the temp metadata directory."""
        return self.DUCKDB_TEMP_DIRECTORY / self.TEMP_META_DIR_NAME

    @property
    def TEMP_CELLS_DIR(self) -> Path:
        """Provides the absolute path to the temp cells directory."""
        return self.DUCKDB_TEMP_DIRECTORY / self.TEMP_CELLS_DIR_NAME

    @computed_field(return_type=dict[str, Any])
    @property
    def DEFAULT_DB_CONFIG(self) -> dict[str, Any]:
        """Generates the DuckDB config dict based on settings."""
        config = {}
        if self.DUCKDB_TEMP_DIRECTORY:
            config["temp_directory"] = str(self.DUCKDB_TEMP_DIRECTORY)
        if self.DUCKDB_MEMORY_LIMIT:
            config["memory_limit"] = self.DUCKDB_MEMORY_LIMIT
        return config

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = CorpusSettings()

# Ensure temp directories exist
try:
    if settings.DUCKDB_TEMP_DIRECTORY:
        settings.DUCKDB_TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)

    settings.TEMP_META_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_CELLS_DIR.mkdir(parents=True, exist_ok=True)

except PermissionError as e:
    logger.error(f"Permission error creating temp directories: {e}")
except Exception as e:
    logger.error(f"Failed to create temp directories: {e}")

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)

logger.info("Corpus configuration loaded successfully")
logger.info(f"  Corpus DB path: {settings.DEFAULT_DB_PATH}")
logger.info(f"  Data directory: {settings.DATA_DIR}")
