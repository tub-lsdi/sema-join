# SEMA-JOIN Corpus

Standalone corpus ingestion package for the SEMA-JOIN project.

## Overview

This package handles ingestion of table data from JSON files into a DuckDB database. The corpus is used by the main SEMA-JOIN backend for semantic join operations.

**Important:** Corpus ingestion runs locally on your machine, not inside Docker. The resulting `corpus.db` file is then mounted into Docker containers.

## Setup

### 1. Install Dependencies

From the corpus directory:

```bash
cd corpus
uv sync
cd ..
```

This will create a virtual environment and install all required dependencies.

### 2. Prepare Data

Place your JSON files containing table data in `corpus/data/` directory. Each JSON file should contain one table per line in the format:

```json
{"url": "...", "relation": [[row1], [row2], ...]}
```

### 3. Run Ingestion

From the project root, use the Makefile:

```bash
make ingest
```

This will:
1. Run parallel corpus ingestion (`01_ingest_corpus_parallel.py`)
2. Calculate PMI statistics (`02_calculate_stats.py`)
3. Create `corpus.db` in the project root

Or run scripts manually:

```bash
# Standard ingestion (single process)
python corpus/setup_db/01_ingest_corpus.py

# OR parallel ingestion (multi-process, faster for large datasets)
python corpus/setup_db/01_ingest_corpus_parallel.py

# Then calculate statistics
python corpus/setup_db/02_calculate_stats.py
```

This creates:
- Row-level PMI scores (for RS-JP algorithm)
- Column-level PMI scores (for CS-JP-LP algorithm)
- NPMI normalized scores

### 4. Start Docker Services

Once corpus.db is created, you can start the Docker services:

```bash
make build
make up
```

Docker containers will access the corpus.db file via volume mount.

## Configuration

The corpus uses its own configuration in [config.py](config.py). Key settings:

- `DB_PATH`: Database file location (default: `corpus.db` at project root)
- `DATA_DIR`: Input data directory (default: `corpus/data/`)
- `DUCKDB_MEMORY_LIMIT`: Memory limit for DuckDB (default: 10GB)
- `CELL_BATCH_SIZE`: Batch size for cell ingestion (default: 1M)
- `TABLE_BATCH_SIZE`: Batch size for table ingestion (default: 50K)

Settings can be overridden with a `.env` file in the project root directory.

## Database Schema

### tables_meta
- `table_id`: BIGINT (primary key, auto-increment)
- `table_hash`: TEXT (unique hash of table contents)
- `source_file`: TEXT (source JSON file path)
- `url`: TEXT (original URL if available)

### cells
- `table_id`: BIGINT (references tables_meta)
- `row_id`: INTEGER
- `col_id`: INTEGER
- `value`: TEXT (cell value)

### Statistics Tables

Created by `02_calculate_stats.py`:
- `values_index`: Value frequency counts
- `row_cooccurrences`: Row-level co-occurrence counts
- `pmi_scores`: Row-level PMI scores
- `npmi_scores`: Normalized PMI scores
- `column_cooccurrences`: Column-level co-occurrence counts
- `column_pmi_scores`: Column-level PMI scores

## Output

The corpus database (`corpus.db`) is created at the project root level and is used by the main backend application.
