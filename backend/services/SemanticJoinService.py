"""
Semantic Join Service class with integrated RS-JP and CS-JP-LP join algorithms.
"""

import duckdb
import polars as pl
from typing import Literal
from backend.utils.normalization import DEFAULT_NORMALIZATION_STRATEGY
from backend.services.algorithms import RSJPAlgorithm, CSJPLPAlgorithm

# Type alias for join methods
JoinMethod = Literal["row", "column"]


class SemanticJoinService:
    """
    Service class that implements semantic join functionality.
    """

    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        """
        Initialize the semantic join service.

        Args:
            db_connection: Database connection (created in main.py)
        """
        self.db_connection = db_connection
        # Use the same normalization strategy as corpus ingestion
        self.normalizer = DEFAULT_NORMALIZATION_STRATEGY

        # Initialize algorithm instances
        self.rs_jp_algorithm = RSJPAlgorithm(db_connection)
        self.cs_jp_algorithm = CSJPLPAlgorithm(db_connection)

    def _normalize(self, value: str) -> str:
        """
        Normalize a value using the same strategy as corpus ingestion.

        Args:
            value: Raw value to normalize

        Returns:
            Normalized value
        """
        return self.normalizer.normalize(value)

    def create_bridge_table(
        self,
        list_r: list[str],
        list_s: list[str],
        join_method: JoinMethod = "row",
    ) -> list[dict]:
        """
        Create a bridge table using the specified join algorithm.

        Args:
            list_r: First list of strings (R set - to be matched)
            list_s: Second list of strings (S set - candidates)
            join_method: "row" for RS-JP or "column" for CS-JP

        Returns:
            List of dictionaries with r_val, s_val, and pmi/score fields

        Raises:
            ValueError: If either list is empty or join_method is invalid
        """
        # Validation
        if not list_r:
            raise ValueError("list_r cannot be empty")
        if not list_s:
            raise ValueError("list_s cannot be empty")
        if join_method not in ["row", "column"]:
            raise ValueError(
                f"join_method must be 'row' or 'column', got '{join_method}'"
            )

        # Normalize input values to match database normalization
        normalized_r = [self._normalize(v) for v in list_r]
        normalized_s = [self._normalize(v) for v in list_s]

        # Delegate to appropriate algorithm
        if join_method == "row":
            return self.rs_jp_algorithm.create_bridge(normalized_r, normalized_s)
        else:  # join_method == "column"
            return self.cs_jp_algorithm.create_bridge(normalized_r, normalized_s)

    def perform_join_from_bridge(
        self,
        list_r: list[dict],
        r_join_col: str,
        bridge_table: list[dict],
        list_s: list[dict],
        s_join_col: str,
    ) -> list[dict]:
        """
        Perform a three-way join using a bridge table.

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

        # normalize values before joining using Polars and the classes normalization method
        r_normalized_col = "r_normalized_join_key"
        s_normalized_col = "s_normalized_join_key"
        list_r_normalized = pl.DataFrame(list_r).with_columns(
            pl.col(r_join_col)
            .map_elements(self._normalize, return_dtype=pl.String)
            .alias(r_normalized_col)
        )

        list_s_normalized = pl.DataFrame(list_s).with_columns(
            pl.col(s_join_col)
            .map_elements(self._normalize, return_dtype=pl.String)
            .alias(s_normalized_col)
        )

        # Register inputs as temp tables using Polars
        conn.register("temp_r", list_r_normalized)
        conn.register("temp_bridge", pl.DataFrame(bridge_table))
        conn.register("temp_s", list_s_normalized)

        # Perform three-way join
        # Bridge table has normalized values
        join_query = f"""
            SELECT 
                r.*,
                bridge.r_val,
                bridge.s_val,
                bridge.pmi,
                s.*
            FROM temp_r AS r
            INNER JOIN temp_bridge AS bridge
                ON r.{r_normalized_col} = bridge.r_val
            INNER JOIN temp_s AS s
                ON s.{s_normalized_col} = bridge.s_val
            ORDER BY r.{r_join_col}
        """

        result_df = conn.execute(join_query).pl()

        # Clean up temp tables
        conn.unregister("temp_r")
        conn.unregister("temp_bridge")
        conn.unregister("temp_s")

        # Drop the helper columns
        final_df = result_df.drop([r_normalized_col, s_normalized_col])

        return final_df.to_dicts()

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
