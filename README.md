# SEMA-JOIN

Semantic table joins using PMI-based matching.

**📚 [Full Documentation](https://tub-lsdi.github.io/sema-join-docs/)**

## Prerequisites

- Docker & docker-compose
- Ollama (for AI features)

## Setup

1. Create `.env` file (copy from example below)
2. Build and start services:
```bash
make build
make up
```

3. Setup Ollama (if not installed):
```bash
make setup-ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

4. Ingest corpus data (if you have `backend/corpus/data/tables.json`):
```bash
make ingest
```

5. Run database migrations:
```bash
make db-migrate
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Commands

```bash
make help          # Show all commands
make build         # Build all images
make up            # Start services
make down          # Stop services
make logs          # View logs
make restart       # Restart services
make ingest        # Ingest corpus data
make db-migrate    # Run database migrations
make clean         # Remove all containers/volumes
```

## Environment (.env)

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

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300

# Go Service
GO_SERVICE_URL=http://localhost:8080
```

## Project Structure

- `/backend` - FastAPI backend
- `/frontend` - Next.js frontend
- `/go-service` - PMI calculation service
