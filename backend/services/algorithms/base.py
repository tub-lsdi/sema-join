"""
Abstract base class for semantic join algorithms.
"""
from abc import ABC, abstractmethod
import duckdb


class BridgeAlgorithm(ABC):
    """Abstract base class for bridge table creation algorithms."""
    
    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        """
        Initialize the algorithm with a database connection.
        
        Args:
            db_connection: DuckDB connection for corpus statistics
        """
        self.db_connection = db_connection
    
    @abstractmethod
    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        Create a bridge table connecting values from list_r to list_s.
        
        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            
        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
        """
        pass

