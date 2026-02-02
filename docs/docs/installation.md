---
sidebar_position: 2
---

# Installation

This guide walks you through installing Project SEMA-JOIN on your system.

## System Requirements

Ensure your system meets these requirements:

- Docker & Docker Compose
- Python 3.10 or higher
- uv package manager for Python
- Ollama (optional, for AI features)

## Installation Steps

### Step 1: Clone the Repository

Download the Project SEMA-JOIN source code to your local machine:

```bash
git clone https://github.com/tub-lsdi/sema-join.git
cd sema-join
```

### Step 2: Configure Environment

Create a `.env` file in the project root with your configuration settings.

**Note:** The project includes a `.env.example` file that you can copy and modify:
```bash
cp .env.example .env
```

Example `.env` configuration:

```bash
# Database
DB_PATH=corpus.db  # Path where DuckDB corpus database will be stored
LOG_LEVEL=DEBUG    # Options: DEBUG, INFO, WARNING, ERROR

# DuckDB Performance Settings
DUCKDB_MEMORY_LIMIT=25GB      # Max RAM DuckDB can use (set to ~75% of available system RAM, e.g., 12GB, 24GB, 48GB)
DUCKDB_TEMP_DIRECTORY=./_temp # Directory for temporary files (requires free disk space during corpus ingestion)

# Corpus Ingestion Batch Sizes
CELL_BATCH_SIZE=1000000  # Number of cells to process per batch (increase if you have more RAM available)
TABLE_BATCH_SIZE=50000   # Number of tables to process per batch (increase if you have more RAM available)

# MySQL Application Database
APP_DB_CONTAINER_NAME="sema_app_db"  # Name for the MySQL Docker container
APP_DB_HOST="localhost"              # Use "localhost" for host access, Docker overrides this to "mysql" internally
APP_DB_PORT="3306"                   # MySQL port
APP_DB_DATABASE="sema_app_db"        # Database name
APP_DB_USERNAME="semajoin"           # MySQL username
APP_DB_PASSWORD="semajoin"           # MySQL password (change in production!)
APP_DB_ROOT_PASSWORD="rootpassword"  # MySQL root password (change in production!)

# Ollama AI
# Runs natively on host for GPU access. Start with: OLLAMA_HOST=0.0.0.0:11434 ollama serve
# Install first: make setup-ollama
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
OLLAMA_MODEL=mistral                    # AI model name (mistral, llama2, etc.)
OLLAMA_TIMEOUT=300                      # Request timeout in seconds

# Go PMI Service
GO_SERVICE_URL=http://localhost:8080  # Go service URL (Docker overrides this internally)
```

### Step 3: Install Dependencies

Install the corpus ingestion dependencies:

```bash
cd corpus
uv sync
cd ..
```

### Step 4.1 **Download pre-built databases**
If you want to ingest data from JSON files, proceed with step 4.2. If you already have a database, adding the path to it in the `.env` file is sufficient.
You may also download our pre-built databases from:

1. **Wiki Corpus**: https://tubcloud.tu-berlin.de/s/XYDeqCGcC25pWKg
2. **Git Tables Corpus**: https://tubcloud.tu-berlin.de/s/y7rYRZR74ECAjs3

The downloaded files are .zip archives. Extract them first, then place it at the location you specified in the `.env` file.
You can continure from step 6.

### Step 4.2 **Create data directory and add corpus data**

First, create the data directory:
```bash
mkdir -p corpus/data
```

You can use the Wikipedia Tables dataset ("A dataset of 1.6M Wikipedia Tables in JSON format") from:

📥 http://websail-fe.cs.northwestern.edu/TabEL/

Add corpus JSON files to the `corpus/data/` directory. The expected structure looks like:

```
# Example structure:
# corpus/data/tables.json
# corpus/data/table_0001.json
# corpus/data/table_0002.json
```

### Step 5: Ingest Corpus Data

Run the corpus ingestion to build the semantic relationship database:

```bash
# Run from project root (sema-join/)
make ingest
```

This runs a parallel ingestion process in three phases:
- **Phase 1**: Process JSON files in parallel, extract table data to temporary Parquet files
- **Phase 2**: Ingest Parquet data into DuckDB (tables_meta and cells tables)
- **Phase 3**: Create database indexes for fast querying
- Result: `corpus.db` created in the project root

### Step 6: Build and Start Services

Build Docker images and start all services:

```bash
# Run from project root (sema-join/)
make build
make up
```

This will:
- Build the backend (Python/FastAPI), frontend (Next.js), and Go service containers
- Start MySQL database for application data
- Launch all services using docker-compose

**Services Started:**
- **Backend Service**: Python/FastAPI application that implements the join algorithms and coordinates operations (port 8000)
- **Go Service**: High-performance PMI calculation engine using optimized bitmap operations (port 8080)
- **Frontend**: Next.js web interface (port 3000)
- **MySQL Database**: Stores application data, uploaded tables, and join history (port 3306)

### Step 7: Install AI Service (Optional)

The AI-powered column matching feature requires Ollama with the Mistral model.

Install Ollama:

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

Or use the make command:
```bash
# Run from project root (sema-join/)
make setup-ollama
```

Pull the Mistral model and start Ollama:
```bash
ollama pull mistral
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## Troubleshooting

**Port Conflicts**
Ensure the following ports are available before starting:
- Port 3000: Frontend (Next.js)
- Port 8000: Backend API (FastAPI)
- Port 8080: Go service (PMI calculations)
- Port 3306: MySQL database
- Port 11434: Ollama AI service (optional)

**Go Service Not Responding**
If PMI calculations fail or the Go service is not accessible:
1. Check if the Go service container is running: `docker ps | grep go-service`
2. View Go service logs: `docker logs sema-join-go-service-1`
3. Verify the corpus database exists at the path specified in `.env` (DB_PATH)

**AI Features Not Working**
The AI-powered column matching requires Ollama to be running on port 11434. Start Ollama with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`.

## Next Steps

After installation, you can start using the application. See [Using SEMA-JOIN](./using-sema-join) to learn how to perform semantic joins.
