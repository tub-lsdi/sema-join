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

    # DuckDB corpus database (read-only access)
    DB_PATH: str = "corpus.db"
    DUCKDB_MEMORY_LIMIT: str = "10GB"

    LOG_LEVEL: str = "DEBUG"

    # Ollama AI settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 60

    # Go Service settings
    GO_SERVICE_URL: str = "http://localhost:8080"

    @property
    def DEFAULT_DB_PATH(self) -> Path:
        """Provides the absolute path to the corpus database file."""
        return self.PROJECT_ROOT / self.DB_PATH

    @computed_field(return_type=dict[str, Any])
    @property
    def DEFAULT_DB_CONFIG(self) -> dict[str, Any]:
        """Generates the DuckDB config dict for corpus database access."""
        config = {}
        if self.DUCKDB_MEMORY_LIMIT:
            config["memory_limit"] = self.DUCKDB_MEMORY_LIMIT
        return config

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)

logger.debug("Configuration loaded successfully:")
logger.debug(f"  Default DuckDB path set to: {settings.DEFAULT_DB_PATH}")

if settings.DEFAULT_DB_CONFIG:
    logger.debug("  DuckDB config:")
    for key, value in settings.DEFAULT_DB_CONFIG.items():
        logger.debug(f"    {key} = '{value}'")
