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
    logger.info("✅ Created row_cooccurrences.")

    # --- 3. Pre-compute PMI Scores (RS-JP) ---
    # Get total number of tables (n)
    logger.info("⏳ Pre-computing row-level PMI scores (for RS-JP)...")
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
    logger.info("✅ Created npmi_scores.")
    return


def calculate_stats_cs(con: duckdb.DuckDBPyConnection) -> None:
    # --- 1. Compute Column-Pair Co-occurrences for CS-JP ---
    # For CS-JP: Count how often value pairs (v1,v2) and (v3,v4) appear in same column pair
    logger.info("⏳ Computing column-pair co-occurrences (for CS-JP)...")
    logger.info("   This may take a while for large corpora...")

    con.execute("DROP TABLE IF EXISTS column_pair_cooccurrences;")
    con.execute("""
                CREATE TABLE column_pair_cooccurrences AS
                SELECT LEAST(c1.value, c2.value, c3.value, c4.value) AS v1,
                       CASE
                           WHEN c1.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN c2.value
                           WHEN c2.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN c1.value
                           WHEN c3.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN c4.value
                           ELSE c3.value
                           END                                       AS v2,
                       CASE
                           WHEN c1.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c3.value < c4.value THEN c3.value ELSE c4.value END
                           WHEN c2.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c3.value < c4.value THEN c3.value ELSE c4.value END
                           WHEN c3.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c1.value < c2.value THEN c1.value ELSE c2.value END
                           ELSE
                               CASE WHEN c1.value < c2.value THEN c1.value ELSE c2.value END
                           END                                       AS v3,
                       CASE
                           WHEN c1.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c3.value < c4.value THEN c4.value ELSE c3.value END
                           WHEN c2.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c3.value < c4.value THEN c4.value ELSE c3.value END
                           WHEN c3.value = LEAST(c1.value, c2.value, c3.value, c4.value) THEN
                               CASE WHEN c1.value < c2.value THEN c2.value ELSE c1.value END
                           ELSE
                               CASE WHEN c1.value < c2.value THEN c2.value ELSE c1.value END
                           END                                       AS v4,
                       COUNT(DISTINCT c1.table_id)                   AS num_tables
                FROM cells c1
                         JOIN cells c2 ON c1.table_id = c2.table_id
                    AND c1.row_id = c2.row_id
                    AND c1.col_id < c2.col_id
                         JOIN cells c3 ON c1.table_id = c3.table_id
                    AND c1.col_id = c3.col_id
                    AND c1.row_id < c3.row_id
                         JOIN cells c4 ON c1.table_id = c4.table_id
                    AND c2.col_id = c4.col_id
                    AND c3.row_id = c4.row_id
                WHERE c1.value != c2.value
                  AND c3.value != c4.value
                  AND (c1.value != c3.value OR c2.value != c4.value)
                GROUP BY v1, v2, v3, v4
                HAVING num_tables >= 2
                """)
    con.commit()
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_colpair_v1v2v3v4 ON column_pair_cooccurrences(v1, v2, v3, v4);"
    )
    con.commit()
    logger.info("Created column_pair_cooccurrences.")

    # --- 2. Pre-compute Column-Level Scores (CS-JP) ---
    logger.info("Pre-computing column-level scores (for CS-JP)...")
    con.execute("DROP TABLE IF EXISTS column_scores;")
    con.execute(f"""
    CREATE TABLE column_scores AS
    SELECT
        cp.v1,
        cp.v2,
        cp.v3,
        cp.v4,
        cp.num_tables,
        LOG(({N} * cp.num_tables) / 
            (GREATEST(rc1.num_tables, 1) * GREATEST(rc2.num_tables, 1))) AS score
    FROM column_pair_cooccurrences cp
    LEFT JOIN row_cooccurrences rc1 
        ON (cp.v1 = rc1.v1 AND cp.v2 = rc1.v2) OR (cp.v1 = rc1.v2 AND cp.v2 = rc1.v1)
    LEFT JOIN row_cooccurrences rc2
        ON (cp.v3 = rc2.v1 AND cp.v4 = rc2.v2) OR (cp.v3 = rc2.v2 AND cp.v4 = rc2.v1);
    """)
    con.commit()
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_colscores_v1v2v3v4 ON column_scores(v1, v2, v3, v4);"
    )
    con.commit()
    logger.info("Created column_scores (CS-JP).")
    return


if __name__ == "__main__":
    main()
