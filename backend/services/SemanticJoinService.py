import duckdb
import polars as pl
from typing import Literal, Optional, TYPE_CHECKING
from backend.utils.normalization import DEFAULT_NORMALIZATION_STRATEGY
from backend.services.algorithms import RSJPAlgorithm, CSJPLPAlgorithm

if TYPE_CHECKING:
    from backend.services.AppDatabaseService import AppDatabaseService

JoinMethod = Literal["row", "column"]


class SemanticJoinService:
    """Handles semantic joins between tables using PMI-based algorithms."""

    def __init__(
        self,
        db_connection: duckdb.DuckDBPyConnection,
        app_database_service: Optional["AppDatabaseService"] = None,
    ):
        self.db_connection = db_connection
        self.app_database_service = app_database_service
        self.normalizer = DEFAULT_NORMALIZATION_STRATEGY
        self.rs_jp_algorithm = RSJPAlgorithm(db_connection)
        self.cs_jp_algorithm = CSJPLPAlgorithm()

    def _normalize(self, value: str) -> str:
        return self.normalizer.normalize(value)

    def create_bridge_table(
        self,
        list_r: list[str],
        list_s: list[str],
        join_method: JoinMethod = "row",
        top_k: int = 1,
    ) -> list[dict]:
        """Create bridge table with r_val, s_val, and npmi/pmi scores."""
        if not list_r or not list_s:
            raise ValueError("Input lists cannot be empty")
        if join_method not in ["row", "column"]:
            raise ValueError(f"Invalid join_method: {join_method}")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        normalized_r = [self._normalize(v) for v in list_r]
        normalized_s = [self._normalize(v) for v in list_s]

        if join_method == "row":
            return self.rs_jp_algorithm.create_bridge(normalized_r, normalized_s, top_k)

        # CS-JP: Test both directions, pick better one
        result_r_to_s = self.cs_jp_algorithm.create_bridge(normalized_r, normalized_s)
        result_s_to_r = self.cs_jp_algorithm.create_bridge(normalized_s, normalized_r)

        score_r_to_s = sum(entry["npmi"] for entry in result_r_to_s)
        score_s_to_r = sum(entry["npmi"] for entry in result_s_to_r)

        if score_r_to_s >= score_s_to_r:
            return result_r_to_s

        # Swap r_val and s_val in result
        return [
            {"r_val": entry["s_val"], "s_val": entry["r_val"], "npmi": entry["npmi"]}
            for entry in result_s_to_r
        ]

    def perform_join_from_bridge(
        self,
        table_r_id: int,
        r_join_col: str,
        bridge_table: list[dict],
        table_s_id: int,
        s_join_col: str,
    ) -> tuple[list[dict], int]:
        """
        Three-way join: R JOIN bridge ON r_join_col JOIN S ON s_join_col.
        Returns (result, total_r_records).
        """
        if not self.app_database_service:
            raise ValueError("AppDatabaseService not available")

        list_r = self.app_database_service.get_table_data(table_r_id)
        list_s = self.app_database_service.get_table_data(table_s_id)

        if not list_r:
            raise ValueError(f"Table R with ID {table_r_id} not found")
        if not list_s:
            raise ValueError(f"Table S with ID {table_s_id} not found")
        if not bridge_table:
            raise ValueError("bridge_table cannot be empty")
        if r_join_col not in list_r[0]:
            raise ValueError(f"Column '{r_join_col}' not found in table R")
        if s_join_col not in list_s[0]:
            raise ValueError(f"Column '{s_join_col}' not found in table S")

        # Add normalized columns for joining
        r_norm_col = "r_normalized_join_key"
        s_norm_col = "s_normalized_join_key"

        df_r = pl.DataFrame(list_r).with_columns(
            pl.col(r_join_col)
            .map_elements(self._normalize, return_dtype=pl.String)
            .alias(r_norm_col)
        )
        df_s = pl.DataFrame(list_s).with_columns(
            pl.col(s_join_col)
            .map_elements(self._normalize, return_dtype=pl.String)
            .alias(s_norm_col)
        )

        # Register and join in DuckDB
        conn = self.db_connection
        conn.register("temp_r", df_r)
        conn.register("temp_bridge", pl.DataFrame(bridge_table))
        conn.register("temp_s", df_s)

        query = f"""
            SELECT r.*, bridge.r_val, bridge.s_val, bridge.npmi, s.*
            FROM temp_r AS r
            JOIN temp_bridge AS bridge ON r.{r_norm_col} = bridge.r_val
            JOIN temp_s AS s ON s.{s_norm_col} = bridge.s_val
            ORDER BY r.{r_join_col}
        """

        result_df = conn.execute(query).pl()
        result_df = result_df.select(
            pl.exclude(["r_val", "s_val", "npmi"]), "r_val", "s_val", "npmi"
        ).drop([r_norm_col, s_norm_col])

        conn.unregister("temp_r")
        conn.unregister("temp_bridge")
        conn.unregister("temp_s")

        result = result_df.to_dicts()

        # Persist to history
        self.app_database_service.save_join_history(
            table_r_id=table_r_id,
            table_s_id=table_s_id,
            bridge_table=bridge_table,
            result=result,
            r_join_col=r_join_col,
            s_join_col=s_join_col,
        )

        return result, len(list_r)

    def validate_inputs(self, list_r: list[str], list_s: list[str]) -> tuple[bool, str]:
        """Validate that both lists are non-empty and contain only strings."""
        if not list_r:
            return False, "list_r cannot be empty"
        if not list_s:
            return False, "list_s cannot be empty"
        if not all(isinstance(x, str) for x in list_r):
            return False, "All elements in list_r must be strings"
        if not all(isinstance(x, str) for x in list_s):
            return False, "All elements in list_s must be strings"
        return True, ""
