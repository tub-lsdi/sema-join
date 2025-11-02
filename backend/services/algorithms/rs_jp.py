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
        top_k: int = 1,
    ) -> list[dict]:
        """
        Create a bridge table using RS-JP algorithm.
        
        Greedy algorithm: Each r independently picks its best s based on row-level PMI.
        
        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            top_k: Number of top candidates to return per R value
            
        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
        """
        conn = self.db_connection

        # Use Polars to efficiently register inputs as temp tables
        conn.register("input_r", pl.DataFrame({"r_val": list_r}))
        conn.register("input_s", pl.DataFrame({"s_val": list_s}))

        # Query to get top_k highest PMI candidates for each r_val
        bridge_query = f"""
            WITH all_candidates AS (
                SELECT
                    r.r_val,
                    s.s_val,
                    npmi.npmi,
                    ROW_NUMBER() OVER (PARTITION BY r.r_val ORDER BY npmi.npmi DESC) as rn
                FROM input_r AS r
                JOIN npmi_scores AS npmi
                    ON r.r_val = npmi.v1 OR r.r_val = npmi.v2
                JOIN input_s AS s
                    ON (s.s_val = npmi.v1 OR s.s_val = npmi.v2)
                WHERE
                    ((r.r_val = npmi.v1 AND s.s_val = npmi.v2) OR
                     (r.r_val = npmi.v2 AND s.s_val = npmi.v1))
                    AND npmi.pmi > 0
            )
            SELECT
                r_val,
                s_val,
                npmi,
            FROM all_candidates
            WHERE rn <= {top_k}
            ORDER BY r_val, npmi DESC
        """
        bridge_df = conn.execute(bridge_query).pl()
        return bridge_df.to_dicts()

