# SEMA-JOIN Project

Implementation of the SEMA-JOIN paper for semantic table joins.

## Project Structure

* `/src/sema_join`: The core Python library. Contains parsing, DB logic, and the join algorithms.
* `/scripts`: Executable, one-time-use scripts for data processing.
* `/data/corpus`: Location for input JSON (NDJSON) table files.
* `/data/db`: Location for the generated DuckDB database.

## Prerequisites
- Python 3.13
- uv

## Setup
1. run `uv sync` to create virtual environment and install dependencies
2. Activate the virtual environment (if this is not done automatically): `source .venv/bin/activate`
## Workflow

This project has a two-stage workflow:

### 1. Offline Pre-processing

Run these scripts *once* to build the database and statistics.

**Step 1: Ingest Corpus**
This script reads all `.json` files from `data/corpus`, normalizes the data,
and inserts all unique tables and their cells into the DuckDB database. It expects `.json` files that contains one 
json structure per line.

```bash
python scripts/01_ingest_corpus.py
```

**Step 2: Calculate Statistics**
This script uses the ingested cell data to build the aggregate tables (values_index, row_cooccurrences) 
and pre-computes the final pmi_scores table.

```bash
python scripts/02_calculate_stats.py
```

**Step 3: Joining**
After pre-processing, the src library can be used by any app (Streamlit, API, etc.) to perform fast, on-demand joins.
An example script is provided:
```bash
python scripts/03_run_join_rsjp.py
```

## Database Schema
```
cells:
    table_id: BIGINT(64)
    row_id: INTEGER
    col_id: INTEGER
    value: VARCHAR(0)
    
pmi_scores: 
    v1: VARCHAR(0)
    v2: VARCHAR(0)
    num_tables_pair: BIGINT(64)
    num_tables_v1: BIGINT(64)
    num_tables_v2: BIGINT(64)
    pmi: DOUBLE(53)
    
row_cooccurrences:
    v1: VARCHAR(0)
    v2: VARCHAR(0)
    num_tables: BIGINT(64)
    
tables_meta:
    table_id: BIGINT(64) NN
    table_hash: VARCHAR(0)
    source_file: VARCHAR(0)
    url: VARCHAR(0)
    + keys
        #1: PK (table_id)
        
values_index:
    value: VARCHAR(0)
    num_tables: BIGINT(64)
```