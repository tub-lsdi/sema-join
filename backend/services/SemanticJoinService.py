"""
Semantic Join Service class with integrated RS-JP join algorithm.
"""
import duckdb
import polars as pl
from typing import Optional


class SemanticJoinService:
    """
    Service class that implements semantic join functionality.
    
    This class provides the RS-JP join algorithm with precomputed PMI scores
    and can be extended with additional business logic, caching, or validation.
    """
    
    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        """
        Initialize the semantic join service.
        
        Args:
            db_connection: Database connection (created in main.py)
        """
        self.db_connection = db_connection
    
    def _get_pmi_score(self, v1: str, v2: str, con: duckdb.DuckDBPyConnection) -> float:
        """
        Private helper to lookup a precomputed PMI score.
        
        Args:
            v1: First value
            v2: Second value
            con: Database connection
            
        Returns:
            PMI score or negative infinity if not found
        """
        q = con.execute(
            """
            SELECT pmi FROM pmi_scores
            WHERE v1 = ? AND v2 = ?
            """,
            (min(v1, v2), max(v1, v2)),
        )
        row = q.fetchone()
        return row[0] if row else float("-inf")
    
    def create_bridge_table(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        Create a bridge table with all candidate matches and PMI scores.
        
        Args:
            list_r: First list of strings (R set - to be matched)
            list_s: Second list of strings (S set - candidates)
            
        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
            
        Raises:
            ValueError: If either list is empty
        """
        # Validation
        if not list_r:
            raise ValueError("list_r cannot be empty")
        if not list_s:
            raise ValueError("list_s cannot be empty")
        
        # Use the database connection from main.py
        conn = self.db_connection

        # Use Polars to efficiently register inputs as temp tables
        conn.register("input_r", pl.DataFrame({"r_val": list_r}))
        conn.register("input_s", pl.DataFrame({"s_val": list_s}))

        # Query to get all candidate matches with PMI scores
        bridge_query = """
            SELECT
                r.r_val,
                s.s_val,
                pmi.pmi
            FROM input_r AS r
            JOIN pmi_scores AS pmi
                ON r.r_val = pmi.v1 OR r.r_val = pmi.v2
            JOIN input_s AS s
                ON (s.s_val = pmi.v1 OR s.s_val = pmi.v2)
            WHERE
                (r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                (r.r_val = pmi.v2 AND s.s_val = pmi.v1)
                AND pmi.pmi > 0
            ORDER BY r.r_val, pmi.pmi DESC
        """
        bridge_df = conn.execute(bridge_query).pl()
        return bridge_df.to_dicts()
    
    def perform_join_from_bridge(
        self,
        list_r: list[str],
        bridge_table: list[dict],
    ) -> dict[str, Optional[str]]:
        """
        Perform a join using a pre-computed bridge table.
        
        Args:
            list_r: List of values from R set
            bridge_table: Pre-computed bridge table with r_val, s_val, pmi
            
        Returns:
            Dictionary mapping each R value to its best matching S value
        """
        if not list_r:
            raise ValueError("list_r cannot be empty")
        
        # Group by r_val and find best match (highest PMI)
        join_map = {}
        for entry in bridge_table:
            r_val = entry["r_val"]
            s_val = entry["s_val"]
            
            # Since bridge_table is ordered by PMI DESC, first occurrence is best
            if r_val not in join_map:
                join_map[r_val] = s_val
        
        # Add back r_values that had no match, setting them to None
        for r in list_r:
            if r not in join_map:
                join_map[r] = None
        
        return join_map
    
    def validate_inputs(self, list_r: list[str], list_s: list[str]) -> tuple[bool, str]:
        """
        Validate input lists for the semantic join operation.
        
        Args:
            list_r: First list of strings
            list_s: Second list of strings
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not list_r:
            return False, "list_r cannot be empty"
        if not list_s:
            return False, "list_s cannot be empty"
        if not all(isinstance(x, str) for x in list_r):
            return False, "All elements in list_r must be strings"
        if not all(isinstance(x, str) for x in list_s):
            return False, "All elements in list_s must be strings"
        
        return True, ""
