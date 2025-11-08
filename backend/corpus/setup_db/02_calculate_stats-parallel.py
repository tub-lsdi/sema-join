import multiprocessing
import os
import shutil
import sys
from curses.textpad import rectangle
from pathlib import Path

from tqdm import tqdm

from backend.config import settings

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import duckdb
from loguru import logger
from backend.services import get_db_connection

def main():
    con = get_db_connection()

    calculate_stats_rs(con)
    con.close()

    # This function manages its own connections for multiprocessing
    calculate_stats_cs()

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


def calculate_stats_cs() -> None: # No 'con' argument
    # --- 1. Compute Column-Pair Co-occurrences for CS-JP ---
    logger.info("Computing column-pair co-occurrences (for CS-JP)...")
    logger.info("This may take a while for large corpora...")

    output_dir = settings.TEMP_COLUMN_PAIRS_DIR
    temp_dir = settings.DUCKDB_TEMP_DIRECTORY
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    worker_db_config = {
        'memory_limit': settings.DUCKDB_MEMORY_LIMIT,
        'temp_directory': str(temp_dir)
    }

    if output_dir.exists():
        logger.warning(f"Cleaning up old chunks dir: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created temporary directory: {output_dir}")

    # --- 2. Fetch Tasks (Connect and Close) ---
    logger.info("Fetching table_ids to process...")
    try:
        # Open a local, temporary connection
        con_fetch = get_db_connection()
        table_ids = con_fetch.execute("SELECT DISTINCT table_id FROM cells").pl()['table_id'].to_list()
        logger.info(f"Found {len(table_ids)} total tables to process.")
    except Exception as e:
        logger.error(f"Could not fetch table_ids from database: {e}")
        return
    finally:
        if "con_fetch" in locals():
            # close local connection to remove lock before workers start
            con_fetch.close()

    logger.info("Task fetching complete. Connection closed.")

    # adjust number of workers if needed
    num_workers = settings.NUM_WORKERS_FOR_CALCULATION
    logger.info(f"Using {num_workers} worker processes.")

    tables_per_chunk = s
    chunks = [table_ids[i:i + tables_per_chunk] for i in range(0, len(table_ids), tables_per_chunk)]
    tasks = []
    for i, chunk in enumerate(chunks):
        output_file = output_dir / f"chunk_{i:05d}.parquet"
        tasks.append((chunk, output_file, settings.DB_PATH, worker_db_config, i))

    logger.info(f"Divided work into {len(tasks)} chunks...")

    # --- 4. Run Pool ---
    logger.info("Starting worker pool...")
    results = []
    context = multiprocessing.get_context('spawn')

    with context.Pool(processes=num_workers) as pool:
        with tqdm(total=len(tasks), desc="Processing table chunks") as pbar:
            for result in pool.imap_unordered(process_table_chunk_wrapper, tasks):
                results.append(result)
                pbar.update(1)

    num_failed = results.count(False)
    if num_failed > 0:
        logger.error(f"{num_failed} chunks failed to process. See error logs.")
    else:
        logger.info("All workers have finished successfully.")

    # --- 5. Ingest Results ---
    logger.info("Ingesting all Parquet chunks...")
    con_ingest = None
    try:
        # Open a new connection for writing
        con_ingest = get_db_connection()

        # UPDATED: Changed table name
        con_ingest.execute("DROP TABLE IF EXISTS all_rectangles_found;")
        con_ingest.execute("""
                           CREATE TABLE all_rectangles_found (
                                                                 table_id BIGINT,
                                                                 pairA_v1 VARCHAR,
                                                                 pairA_v2 VARCHAR,
                                                                 pairB_v1 VARCHAR,
                                                                 pairB_v2 VARCHAR
                           )
                           """)

        rectangle_files = [
            str(f) for f in output_dir.glob("*.parquet")
            if f.is_file() and not f.name.startswith('._')
        ]
        if not rectangle_files:
            logger.warning(f"No Parquet files found to ingest at {output_dir}.")

        else:
            con_ingest.execute(f"""
                INSERT INTO all_rectangles_found
                SELECT * FROM read_parquet({rectangle_files})
            """)
            con_ingest.commit()

        logger.info(f"Ingested all chunks. Cleaning up {output_dir}...")
        shutil.rmtree(output_dir)

        # --- 6. Final Aggregation (using the same 'con_ingest') ---
        logger.info("Starting final aggregation...")
        con_ingest.execute("DROP TABLE IF EXISTS column_cooccurrences;")
        con_ingest.execute("""
                           CREATE TABLE column_cooccurrences AS
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
        con_ingest.commit()
        logger.info("Created column_cooccurrences.")
        con_ingest.execute("DROP TABLE all_rectangles_found;")

        # --- 7. Pre-compute Scores (using the same 'con_ingest') ---
        logger.info("Pre-computing column-level scores (for CS-JP)...")

        con_ingest.execute("DROP TABLE IF EXISTS column_npmi_scores;")
        con_ingest.execute(f"""
            CREATE TABLE column_npmi_scores AS
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
                    -- count(x,y) = |T({{A,B}}, {{C,D}})|
                    cp.num_tables AS rectangle_count,
                    -- count(x) = |T({{A,B}})|
                    rc1.num_tables AS pairA_count,
                    -- count(y) = |T({{C,D}})|
                    rc2.num_tables AS pairB_count,
                    (SELECT N FROM TotalTables) AS N, -- Pass N to the next step

                    -- This is the paper's PMI formula: log( p(x,y) / (p(x) * p(y)) )
                    -- It is rewritten as log( (N * count(x,y)) / (count(x) * count(y)) )
                    LOG( (cp.num_tables * (SELECT N FROM TotalTables)) / 
                         (GREATEST(rc1.num_tables, 1) * GREATEST(rc2.num_tables, 1)) 
                       ) AS pmi_score
                FROM column_cooccurrences cp

                -- DIVERGENCE (Handling Zero Counts):
                -- We use INNER JOIN ('JOIN') to get marginal counts p(x) and p(y).
                -- If a marginal pair's count is 0, its PMI is undefined.
                -- This INNER JOIN correctly and efficiently drops those rectangles.
                JOIN row_cooccurrences rc1 
                    ON cp.pairA_v1 = rc1.v1 AND cp.pairA_v2 = rc1.v2
                JOIN row_cooccurrences rc2 
                    ON cp.pairB_v1 = rc2.v1 AND cp.pairB_v2 = rc2.v2
                WHERE 
                    (cp.num_tables * (SELECT N FROM TotalTables)) > 
                    (rc1.num_tables * rc2.num_tables)
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
                    -- -log(p(joint)) is 0. NPMI should be 1.0.
                    WHEN rectangle_count = N THEN 1.0
                    ELSE pmi_score / (-LOG(rectangle_count::DOUBLE / N))
                END AS npmi_score

            FROM PmiScores;
            """)
        con_ingest.commit()

        con_ingest.execute(
            "CREATE INDEX IF NOT EXISTS idx_column_npmi_all ON column_npmi_scores(pairA_v1, pairA_v2, pairB_v1, pairB_v2);"
        )
        con_ingest.commit()

        logger.info("Created column_npmi_scores (CS-JP).")

    except Exception as e:
        logger.error(f"Error during ingestion/aggregation: {e}")
    finally:
        if con_ingest:
            con_ingest.close()
            logger.info("Ingestion complete. Connection closed.")

    return

def process_table_chunk(table_id_chunk: list[int], output_file: Path, db_path: str, db_config: dict, worker_id: int):
    """
    Worker function to process a chunk of table_ids.
    Connects to DB, runs the query, and saves to Parquet.
    This function runs in a separate process.
    """

    # Handle single-item tuple for SQL IN clause (e.g., IN (123))
    if len(table_id_chunk) == 1:
        table_id_sql = f"({table_id_chunk[0]})"
    else:
        table_id_sql = tuple(table_id_chunk)

    # --- QUERY UPDATED ---
    # Added detailed comments from the new script for clarity.
    # The SQL logic itself was already correct.
    query = f"""
    WITH horizontal_pairs AS (
        -- Find all horizontal pairs (v1, v2) in the same row
        SELECT
            c1.table_id,
            c1.row_id,
            c1.col_id AS col1_id,
            c2.col_id AS col2_id,
            c1.value  AS value1,
            c2.value  AS value2
        FROM cells c1
        JOIN cells c2 ON c1.table_id = c2.table_id
                     AND c1.row_id = c2.row_id
                     -- DIVERGENCE (1/2 for Unordered Sets):
                     -- Canonicalize column order (col1 < col2).
                     -- This prevents finding {{{{A, B}}}} in (col3, col5) AND (col5, col3),
                     -- effectively avoiding double-counting the entire rectangle.
                     AND c1.col_id < c2.col_id
        WHERE c1.table_id IN {table_id_sql}
          -- DIVERGENCE (Semantic Pruning):
          -- Prune semantically uninteresting "self-pairs" (e.g., (A, A)).
          AND c1.value != c2.value
    ),
    rectangles AS (
        -- Find "rectangles" by joining two horizontal pairs on their column_ids
        SELECT
            hp1.table_id,
            -- DIVERGENCE (2/2 for Unordered Sets):
            -- Canonicalize values *within* a pair (e.g., (B, A) -> (A, B)).
            -- This, combined with (col1 < col2), handles our headerless
            -- data by treating (A, B) and (B, A) as the same set {{{{A, B}}}}.
            LEAST(hp1.value1, hp1.value2)  AS p1_v1,
            GREATEST(hp1.value1, hp1.value2) AS p1_v2,
            LEAST(hp2.value1, hp2.value2)  AS p2_v1,
            GREATEST(hp2.value1, hp2.value2) AS p2_v2
        FROM horizontal_pairs hp1
        JOIN horizontal_pairs hp2 ON hp1.table_id = hp2.table_id
                                 AND hp1.col1_id = hp2.col1_id
                                 AND hp1.col2_id = hp2.col2_id
                                 -- Ensure we are joining different rows
                                 AND hp1.row_id < hp2.row_id
        WHERE
            -- DIVERGENCE (Semantic Pruning):
            -- Prune rectangles made of two identical pairs (e.g., ((A,B), (A,B))).
            (hp1.value1 != hp2.value1 OR hp1.value2 != hp2.value2)
    )
    -- Canonicalize the order of the two pairs
    SELECT DISTINCT
        table_id,
        -- Canonicalize the order of the *pairs* to avoid double-counting
        -- the full rectangle, e.g., (Pair {{{{A,B}}}}, Pair {{{{C,D}}}}) is the
        -- same as (Pair {{{{C,D}}}}, Pair {{{{A,B}}}}).
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
    FROM rectangles
    """

    con = None
    try:
        # Each worker creates its own read-only connection
        con = duckdb.connect(database=db_path, config=db_config, read_only=True)
        con.execute("PRAGMA disable_progress_bar;")
        con.execute(f"COPY ({query}) TO '{str(output_file)}' (FORMAT PARQUET);")
        return True

    except Exception as e:
        logger.error(e)
        return False
    finally:
        if con:
            con.close()

def process_table_chunk_wrapper(task_args):
    """
    Helper function to unpack arguments for pool.imap_unordered
    """
    return process_table_chunk(*task_args)


if __name__ == "__main__":
    main()