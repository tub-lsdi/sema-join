import duckdb
from loguru import logger
from sema_join.db import get_db_connection

def main():
    con = get_db_connection()

    # --- 1. Compute Value Counts (|T(r_i)|) ---
    logger.info("⏳ Computing value counts (values_index)...")
    con.execute("DROP TABLE IF EXISTS values_index;")
    con.execute("""
                CREATE TABLE values_index AS
                SELECT
                    value,
                    COUNT(DISTINCT table_id) AS num_tables
                FROM cells
                GROUP BY value
                HAVING num_tables >= 2; -- Pruning: values, must appear in >1 table
                """)
    con.commit()
    logger.info("✅ Created values_index.")

    # --- 2. Compute Co-occurrence Counts (|T(r_i, s_j)|) ---
    logger.info("⏳ Computing row co-occurrences (row_cooccurrences)...")
    con.execute("DROP TABLE IF EXISTS row_cooccurrences;")
    con.execute("""
                CREATE TABLE row_cooccurrences AS
                SELECT
                    LEAST(c1.value, c2.value) AS v1,
                    GREATEST(c1.value, c2.value) AS v2,
                    COUNT(DISTINCT c1.table_id) AS num_tables
                FROM cells c1
                         JOIN cells c2
                              ON c1.table_id = c2.table_id
                                  AND c1.row_id = c2.row_id
                                  AND c1.value < c2.value -- Avoid self-joins and duplicates
                GROUP BY v1, v2
                HAVING num_tables >= 2; -- Pruning: pairs, must appear in >1 table
                """)
    con.commit()
    logger.info("✅ Created row_cooccurrences.")

    # --- 3. Pre-compute PMI Scores ---
    logger.info("⏳ Pre-computing PMI scores...")
    # Get total number of tables (n)
    try:
        N = con.execute("SELECT COUNT(DISTINCT table_id) FROM tables_meta;").fetchone()[0]
    except Exception as e:
        logger.error(f"Could not get table count. Error: {e}")
        return

    if N == 0:
        logger.error("No tables found in tables_meta. Run ingestion script first.")
        return

    logger.info(f"Total tables (N) = {N}")

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
    logger.info("✅ Created pmi_scores.")

    # --- 4. Add Indexes ---
    logger.info("⏳ Creating indexes on values, row-co-occurence and pmi-scores...")
    con.execute("CREATE INDEX IF NOT EXISTS idx_values_val ON values_index(value);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_pairs_v1v2 ON row_cooccurrences(v1, v2);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_pmi_v1v2 ON pmi_scores(v1, v2);")
    con.commit()
    con.close()
    logger.info("✅ All statistics and PMI scores are computed and indexed.")

if __name__ == "__main__":
    main()