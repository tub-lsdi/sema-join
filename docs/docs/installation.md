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

### Step 2: Add Corpus Data

Place your corpus JSON files in the `corpus/data/` directory:

```bash
# Example structure:
# corpus/data/tables.json
# corpus/data/table_0001.json
# corpus/data/table_0002.json
```

These files contain the table data used to build semantic relationships through PMI score calculations.

### Step 3: Install Dependencies

Install the corpus ingestion dependencies:

```bash
cd corpus
uv sync
cd ..
```

### Step 4: Configure Environment

Create a `.env` file in the project root with your configuration settings.

**Note:** The project includes a `.env.example` file that you can copy and modify:
```bash
cp .env.example .env
```

Example `.env` configuration:

```bash
# Database
DB_PATH=corpus.db
LOG_LEVEL=DEBUG
DUCKDB_MEMORY_LIMIT=25GB
DUCKDB_TEMP_DIRECTORY=./_temp

# MySQL
APP_DB_CONTAINER_NAME="sema_app_db"
APP_DB_HOST="localhost"
APP_DB_PORT="3306"
APP_DB_DATABASE="sema_app_db"
APP_DB_USERNAME="semajoin"
APP_DB_PASSWORD="semajoin"
APP_DB_ROOT_PASSWORD="rootpassword"

# Ollama (optional, for AI features)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300

# Go Service
GO_SERVICE_URL=http://localhost:8080
```

### Step 5: Ingest Corpus Data

Run the corpus ingestion to build the semantic relationship database:

```bash
make ingest
```

This will:
- Process all JSON files in `corpus/data/`
- Calculate PMI scores for value pairs
- Create `corpus.db` in the project root

### Step 6: Build and Start Services

Build Docker images and start all services:

```bash
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

### Step 7: Verify Installation

Access the application to verify everything is running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Go Service**: http://localhost:8080 (no web interface, API only)

### Step 8: Install AI Service (Optional)

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

After installation, proceed to corpus ingestion to build the semantic join database.
