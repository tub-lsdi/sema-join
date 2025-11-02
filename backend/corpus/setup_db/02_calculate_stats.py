import os
import sys
from pathlib import Path


# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import duckdb
from loguru import logger
from backend.services import get_db_connection


def main():
    con = get_db_connection()

    calculate_stats_rs(con)
    calculate_stats_cs(con)

    con.close()
    logger.info("All statistics (RS-JP & CS-JP) computed and indexed.")


def calculate_stats_rs(con: duckdb.DuckDBPyConnection) -> None:
    # --- 1. Compute Value Counts (|T(r_i)|) ---
    logger.info("Computing value counts (values_index)...")
    con.execute("DROP TABLE IF EXISTS values_index;")
    con.execute("""
                CREATE TABLE values_index AS
                WITH distinct_values AS (
                    -- Find unique value/table pairs first
                    SELECT DISTINCT value, table_id
                    FROM cells)
                SELECT value,
                       -- Count the distinct pairs
                       COUNT(*) AS num_tables
                FROM distinct_values
                GROUP BY value
                HAVING num_tables >= 2; -- Pruning
                """)
    con.commit()
    con.execute("CREATE INDEX IF NOT EXISTS idx_values_val ON values_index(value);")
    con.commit()
    logger.info("Created values_index")

    # --- 2. Compute Co-occurrence Counts (|T(r_i, s_j)|) ---
    # Filter cells to only those with values in values_index (removing rare values)
    logger.info("Creating temp_filtered_cells...")
    con.execute("DROP TABLE IF EXISTS temp_filtered_cells;")
    con.execute("""
                CREATE TEMPORARY TABLE temp_filtered_cells AS
                SELECT c.table_id, c.row_id, c.value
                FROM cells c
                JOIN values_index v ON c.value = v.value;
                """)
    con.commit()
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_temp_filtered_cells ON temp_filtered_cells(table_id, row_id);"
    )
    con.commit()

    # Log reduction achieved by filtering
    original_count = con.execute("SELECT COUNT(*) FROM cells").fetchone()[0]
    filtered_count = con.execute("SELECT COUNT(*) FROM temp_filtered_cells").fetchone()[
        0
    ]
    reduction_percent = ((original_count - filtered_count) / original_count) * 100
    logger.debug(
        f"Removed {original_count - filtered_count:,} rows (a {reduction_percent:.2f}% reduction)."
    )
    # Compute row co-occurrences based on filtered cells
    # pairs are canonicalized, v1 < v2
    logger.info("Computing row co-occurrences (row_cooccurrences)...")
    con.execute("DROP TABLE IF EXISTS row_cooccurrences;")
    con.execute("""
                CREATE TABLE row_cooccurrences AS
                WITH distinct_pairs_by_table AS (SELECT DISTINCT LEAST(c1.value, c2.value)    AS v1,
                                                                 GREATEST(c1.value, c2.value) AS v2,
                                                                 c1.table_id
                                                 FROM temp_filtered_cells c1
                                                          JOIN temp_filtered_cells c2
                                                               ON c1.table_id = c2.table_id
                                                                   AND c1.row_id = c2.row_id
                                                                   AND c1.value < c2.value)
                SELECT v1,
                       v2,
                       COUNT(*) AS num_tables
                FROM distinct_pairs_by_table
                GROUP BY v1, v2
                HAVING num_tables >= 2;
                """)
    con.commit()

    # Clean up temp tables
    con.execute("DROP TABLE IF EXISTS temp_filtered_cells;")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_pairs_v1v2 ON row_cooccurrences(v1, v2);"
    )
    con.commit()
    logger.info("Created row_cooccurrences.")

    # --- 3. Pre-compute PMI Scores (RS-JP) ---
    # Get total number of tables (n)
    logger.info("Pre-computing row-level PMI scores (for RS-JP)...")
    try:
        N = con.execute("SELECT COUNT(DISTINCT table_id) FROM tables_meta;").fetchone()[
            0
        ]
    except Exception as e:
        logger.error(f"Could not get table count. Error: {e}")
        return

    if N == 0:
        logger.error("No tables found in tables_meta. Run ingestion script first.")
        return

    logger.debug(f"Total tables (N) = {N}")

    con.execute("DROP TABLE IF EXISTS pmi_scores;")
    con.execute(f"""
        CREATE TABLE pmi_scores AS
        SELECT
            rc.v1,
            rc.v2,
            rc.num_tables AS num_tables_pair,
            v1s.num_tables AS num_tables_v1,
            v2s.num_tables AS num_tables_v2,
            LOG(({N} * rc.num_tables) / (v1s.num_tables * v2s.num_tables)) AS pmi
        FROM row_cooccurrences rc
        JOIN values_index v1s ON rc.v1 = v1s.value
        JOIN values_index v2s ON rc.v2 = v2s.value;
        """)
    con.commit()
    con.execute("CREATE INDEX IF NOT EXISTS idx_pmi_v1v2 ON pmi_scores(v1, v2);")
    con.commit()
    logger.info("Created pmi_scores (RS-JP).")

    # --- 4. Compute Normalized PMI (NPMI) ---
    logger.info("Computing normalized PMI scores (npmi_scores)...")
    con.execute("DROP TABLE IF EXISTS npmi_scores;")
    con.execute(f"""
            CREATE TABLE npmi_scores AS
            SELECT
                v1,
                v2,
                pmi,
                -- Handle the p(x, y) = 1 edge case, which results in 0/0
                CASE
                    WHEN num_tables_pair = {N} THEN 1.0 
                    ELSE pmi / -LOG(num_tables_pair / CAST({N} AS DOUBLE))
                END AS npmi
            FROM pmi_scores;
        """)
    con.commit()

    # Add an index, just like for the other tables
    con.execute("CREATE INDEX IF NOT EXISTS idx_npmi_v1v2 ON npmi_scores(v1, v2);")
    con.commit()
    logger.info("Created npmi_scores for row score.")
    return


def calculate_stats_cs(con: duckdb.DuckDBPyConnection) -> None:
    # --- 1. Compute Column-Pair Co-occurrences for CS-JP ---
    # For CS-JP: Count how often value pairs (v1,v2) and (v3,v4) appear in same column pair
    logger.info("Computing column-pair co-occurrences (for CS-JP)...")
    logger.info("This may take a while for large corpora...")

    # Create aggregation table to store all rectangles found
    con.execute("""
                CREATE TABLE IF NOT EXISTS all_rectangles_found (
                                                                    table_id BIGINT,
                                                                    pairA_v1 VARCHAR,
                                                                    pairA_v2 VARCHAR,
                                                                    pairB_v1 VARCHAR,
                                                                    pairB_v2 VARCHAR
                )
                """)
    # Get all distinct table_ids
    table_ids = con.execute("SELECT DISTINCT table_id FROM cells").pl()['table_id'].to_list()
    logger.info(f"Found {len(table_ids)} tables to process...")

    for i, current_table_id in enumerate(table_ids):

        if (i + 1) % 1000 == 0:
            logger.info(f"Processing table {i+1}/{len(table_ids)} (ID: {current_table_id})...")

        # 2-step join query, but constrained to a SINGLE table_id
        con.execute(f"""
            INSERT INTO all_rectangles_found
            WITH horizontal_pairs AS (
                SELECT
                    c1.row_id,
                    c1.col_id AS col1_id,
                    c2.col_id AS col2_id,
                    c1.value  AS value1,
                    c2.value  AS value2
                FROM cells c1
                JOIN cells c2 ON c1.table_id = c2.table_id
                             AND c1.row_id = c2.row_id
                             AND c1.col_id < c2.col_id
                WHERE c1.table_id = {current_table_id}
                  AND c1.value != c2.value
            ),
            rectangles AS (
                SELECT
                    -- Canonicalize Pair 1 (from hp1)
                    LEAST(hp1.value1, hp1.value2)  AS p1_v1,
                    GREATEST(hp1.value1, hp1.value2) AS p1_v2,
                    -- Canonicalize Pair 2 (from hp2)
                    LEAST(hp2.value1, hp2.value2)  AS p2_v1,
                    GREATEST(hp2.value1, hp2.value2) AS p2_v2
                FROM horizontal_pairs hp1
                JOIN horizontal_pairs hp2 ON hp1.col1_id = hp2.col1_id
                                         AND hp1.col2_id = hp2.col2_id
                                         AND hp1.row_id < hp2.row_id
                WHERE
                    (hp1.value1 != hp2.value1 OR hp1.value2 != hp2.value2)
            )
            -- Canonicalize the order of the two pairs
            SELECT
                {current_table_id} AS table_id,
                CASE
                    WHEN p1_v1 < p2_v1 OR (p1_v1 = p2_v1 AND p1_v2 <= p2_v2) THEN p1_v1
                    ELSE p2_v1
                END AS pairA_v1,
                CASE
                    WHEN p1_v1 < p2_v1 OR (p1_v1 = p2_v1 AND p1_v2 <= p2_v2) THEN p1_v2
                    ELSE p2_v2
                END AS pairA_v2,
                CASE
                    WHEN p1_v1 < p2_v1 OR (p1_v1 = p2_v1 AND p1_v2 <= p2_v2) THEN p2_v1
                    ELSE p1_v1
                END AS pairB_v1,
                CASE
                    WHEN p1_v1 < p2_v1 OR (p1_v1 = p2_v1 AND p1_v2 <= p2_v2) THEN p2_v2
                    ELSE p1_v2
                END AS pairB_v2
            FROM rectangles;
        """)

    logger.info("Loop complete. Starting final aggregation. This will take some memory...")

    con.execute("DROP TABLE IF EXISTS column_pair_cooccurrences;")
    con.execute("""
                CREATE TABLE column_pair_cooccurrences AS
                SELECT
                    pairA_v1,
                    pairA_v2,
                    pairB_v1,
                    pairB_v2,
                    COUNT(DISTINCT table_id) AS num_tables
                FROM all_rectangles_found
                GROUP BY ALL
                HAVING num_tables >= 2
                """)
    logger.info("Created column_pair_cooccurrences.")

    # --- 2. Pre-compute Column-Level Scores (CS-JP) ---
    logger.info("Pre-computing column-level scores (for CS-JP)...")
    con.execute("DROP TABLE IF EXISTS column_scores;")
    con.execute(f"""
        CREATE TABLE column_scores AS
        WITH TotalTables (N) AS (
            -- 1. Get the total number of tables
            SELECT COUNT(DISTINCT table_id) FROM cells
        ),
        PmiScores AS (
            -- 2. Calculate PMI scores for column pairs
            SELECT
                cp.pairA_v1,
                cp.pairA_v2,
                cp.pairB_v1,
                cp.pairB_v2,
                cp.num_tables AS rectangle_count,
                rc1.num_tables AS pairA_count,
                rc2.num_tables AS pairB_count,
                (SELECT N FROM TotalTables) AS N, -- Pass N to the next step

                LOG( (cp.num_tables * (SELECT N FROM TotalTables)) / 
                     (GREATEST(rc1.num_tables, 1) * GREATEST(rc2.num_tables, 1)) 
                   ) AS pmi_score
            FROM column_pair_cooccurrences cp
            JOIN TotalTables ON 1=1 -- Make N available to all rows
            LEFT JOIN row_cooccurrences rc1 
                ON cp.pairA_v1 = rc1.v1 AND cp.pairA_v2 = rc1.v2
            LEFT JOIN row_cooccurrences rc2 
                ON cp.pairB_v1 = rc2.v1 AND cp.pairB_v2 = rc2.v2
            WHERE 
                -- Prune pairs with negative/zero correlation (as per paper)
                (cp.num_tables * (SELECT N FROM TotalTables)) > 
                (GREATEST(rc1.num_tables, 1) * GREATEST(rc2.num_tables, 1))
        )
        -- 3. Normalize PMI to get NPMI
        SELECT
            pairA_v1,
            pairA_v2,
            pairB_v1,
            pairB_v2,
            rectangle_count,
            pairA_count,
            pairB_count,
            pmi_score,

            -- NPMI = PMI / -log(p(joint))
            -- p(joint) = rectangle_count / N
            CASE
                -- Safeguard: If p(joint) = 1 (rectangle is in every table), 
                WHEN rectangle_count = N THEN 1.0
                ELSE pmi_score / (-LOG(rectangle_count::DOUBLE / N))
            END AS npmi_score

        FROM PmiScores;
        """)
    con.commit()
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_colscores_v1v2v3v4 ON column_scores(pairA_v1, pairA_v2, pairB_v1, pairB_v2);"
    )
    con.commit()
    logger.info("Created column_scores (CS-JP).")
    return


if __name__ == "__main__":
    main()
