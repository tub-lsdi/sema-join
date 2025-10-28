"""
RS-JP algorithm implementation.
"""
import polars as pl
from .base import BridgeAlgorithm


class RSJPAlgorithm(BridgeAlgorithm):
    """
    RS-JP algorithm.
    
    Greedy algorithm: Each r independently picks its best s based on row-level PMI.
    Fast and efficient for most use cases.
    """
    
    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        Create a bridge table using RS-JP algorithm.
        
        Greedy algorithm: Each r independently picks its best s based on row-level PMI.
        
        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            
        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
        """
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
                    ((r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                     (r.r_val = pmi.v2 AND s.s_val = pmi.v1))
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

