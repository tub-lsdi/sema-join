"""
Semantic Join Service class with integrated RS-JP join algorithm.
"""
import duckdb
import polars as pl
from typing import Optional


class SemanticJoinService:
    """
    Service class that implements semantic join functionality.

    This class provides the RS-JP join algorithm with precomputed PMI scores.
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
        Create a bridge table with the highest PMI match for each r_val.

        Args:
            list_r: First list of strings (R set - to be matched)
            list_s: Second list of strings (S set - candidates)

        Returns:
            List of dictionaries with r_val, s_val, and pmi fields (only highest PMI per r_val)

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

        # Query to get only the highest PMI candidate for each r_val
        bridge_query = """
            WITH all_candidates AS (
                SELECT
                    r.r_val,
                    s.s_val,
                    pmi.pmi,
                    ROW_NUMBER() OVER (PARTITION BY r.r_val ORDER BY pmi.pmi DESC) as rn
                FROM input_r AS r
                JOIN pmi_scores AS pmi
                    ON r.r_val = pmi.v1 OR r.r_val = pmi.v2
                JOIN input_s AS s
                    ON (s.s_val = pmi.v1 OR s.s_val = pmi.v2)
                WHERE
                    (r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                    (r.r_val = pmi.v2 AND s.s_val = pmi.v1)
                    AND pmi.pmi > 0
            )
            SELECT
                r_val,
                s_val,
                pmi
            FROM all_candidates
            WHERE rn = 1
            ORDER BY r_val
        """
        bridge_df = conn.execute(bridge_query).pl()
        return bridge_df.to_dicts()

    def perform_join_from_bridge(
        self,
        list_r: list[dict],
        r_join_col: str,
        bridge_table: list[dict],
        list_s: list[dict],
        s_join_col: str,
    ) -> list[dict]:
        """
        Perform a three-way join using a pre-computed bridge table.

        This performs: list_r JOIN bridge_table ON r_join_col = r_val
                              JOIN list_s ON s_val = s_join_col

        Args:
            list_r: List of records from R dataset
            r_join_col: Column name in list_r to join with bridge_table.r_val
            bridge_table: Bridge table with r_val, s_val, pmi
            list_s: List of records from S dataset
            s_join_col: Column name in list_s to join with bridge_table.s_val

        Returns:
            List of joined records containing all columns from R, bridge, and S

        Raises:
            ValueError: If inputs are invalid or join columns don't exist
        """
        # Validation
        if not list_r:
            raise ValueError("list_r cannot be empty")
        if not list_s:
            raise ValueError("list_s cannot be empty")
        if not bridge_table:
            raise ValueError("bridge_table cannot be empty")

        # Check if join columns exist
        if r_join_col not in list_r[0]:
            raise ValueError(f"Column '{r_join_col}' not found in list_r")
        if s_join_col not in list_s[0]:
            raise ValueError(f"Column '{s_join_col}' not found in list_s")

        # Use the database connection from main.py
        conn = self.db_connection

        # Register inputs as temp tables using Polars
        conn.register("temp_r", pl.DataFrame(list_r))
        conn.register("temp_bridge", pl.DataFrame(bridge_table))
        conn.register("temp_s", pl.DataFrame(list_s))

        # Perform three-way join
        join_query = f"""
            SELECT 
                r.*,
                bridge.r_val,
                bridge.s_val,
                bridge.pmi,
                s.*
            FROM temp_r AS r
            INNER JOIN temp_bridge AS bridge
                ON r.{r_join_col} = bridge.r_val
            INNER JOIN temp_s AS s
                ON bridge.s_val = s.{s_join_col}
            ORDER BY r.{r_join_col}
        """

        result_df = conn.execute(join_query).pl()

        # Clean up temp tables
        conn.unregister("temp_r")
        conn.unregister("temp_bridge")
        conn.unregister("temp_s")

        return result_df.to_dicts()

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
