import duckdb
import polars as pl
from .db import get_db_connection
from typing import Optional


def _get_pmi_score(v1: str, v2: str, con: duckdb.DuckDBPyConnection) -> float:
    """Private helper to lookup a precomputed PMI score."""
    q = con.execute(
        """
                    SELECT pmi FROM pmi_scores
                    WHERE v1 = ? AND v2 = ?
                    """,
        (min(v1, v2), max(v1, v2)),
    )
    row = q.fetchone()
    return row[0] if row else float("-inf")


def rs_jp_join(R: list[str], S: list[str]) -> dict[str, Optional[str]]:
    """
    Performs an RS-JP join on two lists of values using precomputed stats.

    This is an efficient, database-side implementation.
    """
    conn = get_db_connection()

    # Use Polars to efficiently register inputs as temp tables
    conn.register("input_r", pl.DataFrame({"r_val": R}))
    conn.register("input_s", pl.DataFrame({"s_val": S}))

    query = """
            WITH scored_pairs AS (
                SELECT
                    r.r_val,
                    s.s_val,
                    pmi.pmi
                FROM input_r AS r
                         -- Join to find candidate pairs
                         JOIN pmi_scores AS pmi
                              ON r.r_val = pmi.v1 OR r.r_val = pmi.v2
                    -- Join to filter by S
                         JOIN input_s AS s
                              ON (s.s_val = pmi.v1 OR s.s_val = pmi.v2)
                WHERE
                   -- Ensure the pair is (r, s) not (r1, r2) or (s1, s2)
                    (r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                    (r.r_val = pmi.v2 AND s.s_val = pmi.v1)
                        AND pmi.pmi > 0 -- Per paper, prune negative scores
            ),
                 ranked_pairs AS (
                     SELECT
                         r_val,
                         s_val,
                         pmi,
                         -- For each r_val, find the s_val with the highest PMI
                         ROW_NUMBER() OVER(PARTITION BY r_val ORDER BY pmi DESC) as rn
                     FROM scored_pairs
                 )
            -- Select only the best match (rn=1) for each r_val
            SELECT r_val, s_val
            FROM ranked_pairs
            WHERE rn = 1 \
            """

    # Get the {r: s} map of best joins
    best_joins = conn.execute(query).pl().to_dict(as_series=False)
    join_map = dict(zip(best_joins["r_val"], best_joins["s_val"]))

    # Add back r_values that had no match, setting them to None
    for r in R:
        if r not in join_map:
            join_map[r] = None

    return join_map
