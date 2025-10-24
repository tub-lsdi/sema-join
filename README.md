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
  - use `uv sync --no-dev` to skip dev dependencies
2. Activate the virtual environment (if this is not done automatically): `source .venv/bin/activate`
## Workflow

This project has a two-stage workflow:

### 1. Offline Pre-processing

Run these scripts *once* to build the database and statistics.

**Step 1: Ingest Corpus**
This script reads all `.ndjson` files from `data/corpus`, normalizes the data,
and inserts all unique tables and their cells into the DuckDB database.

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