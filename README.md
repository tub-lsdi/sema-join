# SEMA-JOIN Project

Implementation of the SEMA-JOIN paper for semantic table joins.

**📚 [View Full Documentation](https://tub-lsdi.github.io/sema-join-docs/)**

## Project Structure

* `/backend`: Self-contained FastAPI backend application
  * `/services`: Business logic and algorithms
  * `/routes`: API endpoints
  * `/corpus`: Corpus data and setup scripts
  * `/utils`: Utility functions
* `/frontend`: Next.js web application

## Prerequisites

### For Docker Setup (Recommended)
- Docker and Docker Compose
- Make (for running Makefile commands)

### For Manual Setup
- Python 3.13+
- uv (Python package manager)
- Node.js 20+ and npm
- Docker (for application database)
- Ollama (optional, for AI features)
- Mistral model (optional, via Ollama: `ollama pull mistral`)

## 🚀 Quick Start with Docker (Recommended)

The easiest way to run SEMA-JOIN is using Docker with the provided Makefile:

```bash
# 1. Create .env file with required configuration (see Environment Setup below)
# 2. Start all services
make up

# 3. Run database migrations
make migrate

# 4. (Optional) Ingest corpus data
make ingest

# 5. Access the application:
#    - Frontend: http://localhost:3000
#    - Backend API: http://localhost:8000
#    - API Docs: http://localhost:8000/docs
```

### Available Make Commands

```bash
make up              # Start all services
make down            # Stop all services
make build           # Build all Docker images
make logs            # View logs from all services
make logs-backend    # View backend logs only
make logs-frontend   # View frontend logs only
make migrate         # Run Alembic migrations
make migrate-down    # Rollback one migration
make migrate-create  # Create new migration (usage: make migrate-create MSG='message')
make ingest          # Run corpus ingestion script
make test            # Run tests
make clean           # Stop and remove containers and volumes
make restart         # Restart all services
```

## 🚀 Quick Start (Manual Setup)

We provide a convenient management script for easy setup and running:

```bash
# Make the script executable (first time only)
chmod +x sema-join.sh

# Show help
./sema-join.sh
./sema-join.sh help

# Quick Start:
# 1. Create .env file with required configuration (see Environment Setup below)
# 2. Install all dependencies
./sema-join.sh install all
# 3. Start Docker services (application database)
./sema-join.sh docker run
# 4. Initialize application database schema
./sema-join.sh app_db
# 5. Setup corpus database
./sema-join.sh db
# 6. (Optional) Setup AI (Ollama + Mistral)
./sema-join.sh ai setup
# 7. (Optional) Start Ollama service
./sema-join.sh ai serve
# 8. Run both servers
./sema-join.sh run
```

### Environment Setup

Before running the project, create a `.env` file in the project root with the required configuration:

#### For Docker Setup:

```bash
# External JSON files directory (absolute path on host)
INPUT_DIR=/absolute/path/to/json/files

# Application Database Configuration
APP_DB_CONTAINER_NAME=sema_app_db
APP_DB_HOST=mysql
APP_DB_PORT=3306
APP_DB_DATABASE=sema_app_db
APP_DB_USERNAME=your_username
APP_DB_PASSWORD=your_password
APP_DB_ROOT_PASSWORD=your_root_password

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434

# Other Settings
LOG_LEVEL=DEBUG
DUCKDB_MEMORY_LIMIT=10GB

# Note: DB_PATH is NOT needed - DuckDB is managed by Docker volume at /app/data/corpus.db
```

#### For Manual Setup:

```bash
DB_PATH=corpus.db
LOG_LEVEL=DEBUG

# Application Database Configuration
APP_DB_CONTAINER_NAME=sema_app_db
APP_DB_HOST=localhost
APP_DB_PORT=3306
APP_DB_DATABASE=sema_app_db
APP_DB_USERNAME=your_username
APP_DB_PASSWORD=your_password
APP_DB_ROOT_PASSWORD=your_root_password
```

See the [Environment Setup documentation](https://tub-lsdi.github.io/sema-join-docs/docs/environment-setup) for complete configuration details.

### Available Commands

```bash
# Installation
./sema-join.sh install backend     # Install Python dependencies
./sema-join.sh install frontend    # Install Node.js dependencies
./sema-join.sh install all         # Install everything

# Running
./sema-join.sh run                 # Start both servers
./sema-join.sh run backend         # Start backend only (port 8000)
./sema-join.sh run frontend        # Start frontend only (port 3000)

# Database & Info
./sema-join.sh db                  # Initialize corpus database
./sema-join.sh db --large          # Initialize corpus database with scripts for large corpora
./sema-join.sh app_db              # Run Alembic migrations for application database
./sema-join.sh status              # Check project status
./sema-join.sh help                # Show help

# Docker
./sema-join.sh docker run          # Start Docker services (build & up)
./sema-join.sh docker down         # Stop Docker services

# AI Commands
./sema-join.sh ai setup            # Install Ollama & pull Mistral model
./sema-join.sh ai status           # Check AI status
./sema-join.sh ai serve            # Start Ollama service
```

## Manual Setup (Alternative)

### Backend Setup

#### 1. Install Backend Dependencies
```bash
uv sync --extra backend
```

#### 2. Activate Virtual Environment
Before running any scripts or commands, activate the virtual environment:
```bash
source .venv/bin/activate
```

Or use `uv run` to run commands in the virtual environment without activating it:
```bash
uv run <command>
```

#### 3. Setup Database
Run this once to ingest corpus data and calculate PMI statistics:
```bash
./backend/setup_database.sh
```

Or run the setup scripts individually:
```bash
# Step 1: Ingest corpus data
python backend/corpus/setup_db/01_ingest_corpus.py
# or use the version for larger corpora:
python backend/corpus/setup_db/01_ingest_corpus_parllel.py

# Step 2: Calculate PMI statistics
python backend/corpus/setup_db/02_calculate_stats.py
```

This will create the `corpus.db` database file in the project root.

#### 4. Start the Backend Server
```bash
./backend/run_server.sh
```

Or run directly:
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### Frontend Setup

#### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

#### 2. Start the Development Server
```bash
npm run dev
```

The frontend will be available at: http://localhost:3000

### AI Setup (Optional)


#### 1. Install Ollama

For Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

For macOS:
```bash
brew install ollama
```

For Windows:
- Download Ollama from https://ollama.com/download
- Install and run Ollama

#### 2. Install Mistral Model
```bash
ollama pull mistral
```

#### 3. Start Ollama Service
```bash
ollama serve
```

**Note:** Ollama must be running on port 11434 for AI features to work.
