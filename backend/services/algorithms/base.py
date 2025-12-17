from abc import ABC, abstractmethod
from typing import Optional
import duckdb


class BridgeAlgorithm(ABC):
    """Abstract base class for bridge table creation algorithms."""

    def __init__(
        self,
        db_connection: duckdb.DuckDBPyConnection,
        pmi_service: Optional["PMIService"] = None,
    ):
        """
        Initialize the algorithm with a database connection and optional PMI service.

        Args:
            db_connection: DuckDB connection for corpus statistics
            pmi_service: Optional PMIService instance for fetching row-level PMI scores
        """
        self.db_connection = db_connection
        self.pmi_service = pmi_service

    @abstractmethod
    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
        top_k: int = 1,
    ) -> list[dict]:
        """
        Create a bridge table connecting values from list_r to list_s.

        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            top_k: Number of top candidates to return per R value

        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
        """
        pass
