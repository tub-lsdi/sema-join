# SEMA-JOIN Project

Implementation of the SEMA-JOIN paper for semantic table joins.

## Project Structure

* `/backend`: Self-contained FastAPI backend application
  * `/services`: Business logic
  * `/routes`: API endpoints
  * `/corpus`: Corpus data and setup scripts
* `db.py`: DuckDB database 

## Prerequisites
- Python 3.13
- uv

## Quick Start

### 1. Install Dependencies
```bash
uv sync --extra backend
```

### 2. Activate Virtual Environment
Before running any scripts or commands, activate the virtual environment:
```bash
source .venv/bin/activate
```

Or use `uv run` to run commands in the virtual environment without activating it:
```bash
uv run <command>
```

### 3. Setup Database
Run this once to ingest corpus data and calculate PMI statistics:
```bash
./backend/setup_database.sh
```

This will create the `db.py` database file in the project root.

### 4. Start the API Server
```bash
./backend/run_server.sh
```

The API will be available at: http://localhost:8000

### 5. Test the API
```bash
# View API documentation
open http://localhost:8000/docs

# Or run the example client
python backend/example_client.py
```

## API Endpoints

The API provides a two-step semantic join workflow:

### POST /bridge-table
Creates a bridge table with all candidate matches and PMI scores.
```bash
curl -X POST "http://localhost:8000/bridge-table" \
  -H "Content-Type: application/json" \
  -d '{"list_r": ["US", "UK"], "list_s": ["USA", "United Kingdom"]}'
```

### POST /join-from-bridge
Performs the join using a pre-computed bridge table.
```bash
curl -X POST "http://localhost:8000/join-from-bridge" \
  -H "Content-Type: application/json" \
  -d '{"list_r": ["US", "UK"], "bridge_table": [...]}'
```