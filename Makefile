.PHONY: help build build-backend build-go build-frontend up down restart logs clean ingest db-migrate setup-ollama

# Default target
help:
	@echo "Sema-Join Docker Commands"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build              - Build all Docker images"
	@echo "  make build-backend      - Build backend image only"
	@echo "  make build-go           - Build go-service image only"
	@echo "  make build-frontend     - Build frontend image only"
	@echo ""
	@echo "Runtime Commands:"
	@echo "  make up                 - Start all services"
	@echo "  make down               - Stop all services"
	@echo "  make restart            - Restart all services"
	@echo "  make logs               - View logs from all services"
	@echo ""
	@echo "Database Commands:"
	@echo "  make ingest             - Run corpus ingestion (requires corpus/data/tables.json)"
	@echo "  make db-migrate         - Run Alembic migrations for MySQL"
	@echo ""
	@echo "AI Setup (Run Ollama natively for best performance):"
	@echo "  make setup-ollama       - Install and setup Ollama with mistral model"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean              - Remove all containers, volumes, and images"

# Build targets
build:
	@echo "Building all Docker images (no cache)..."
	docker compose build --no-cache

build-backend:
	@echo "Building backend image (no cache)..."
	docker compose build --no-cache backend

build-go:
	@echo "Building go-service image (no cache)..."
	docker compose build --no-cache go-service

build-frontend:
	@echo "Building frontend image (no cache)..."
	docker compose build --no-cache frontend

# Runtime targets
up:
	@echo "Starting all services..."
	docker compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Go Service: http://localhost:8080"
	@echo ""
	@echo "Note: Ollama should be running natively on your host (port 11434)"
	@echo "If not installed, run: make setup-ollama"
	@echo ""
	@echo "Run 'make logs' to view logs"

down:
	@echo "Stopping all services..."
	docker compose down

restart: down up

logs:
	docker compose logs -f

# Database targets
ingest:
	@echo "Running corpus ingestion locally..."
	@if [ ! -f "corpus/data/tables.json" ]; then \
		echo "Error: corpus/data/tables.json not found"; \
		echo "Please ensure the corpus data file exists before running ingestion."; \
		exit 1; \
	fi
	@if [ ! -d "corpus/.venv" ]; then \
		echo "Error: Corpus virtual environment not found"; \
		echo "Please run 'cd corpus && uv sync && cd ..' first"; \
		exit 1; \
	fi
	@df -h . | tail -1
	@echo ""
	@echo "Phase 1: Ingesting corpus data..."
	corpus/.venv/bin/python corpus/setup_db/01_ingest_corpus_parallel.py
	@echo ""
	@echo "Corpus ingestion complete! Database created at: corpus.db"
	@echo "You can now run 'make build' and 'make up' to start the services."

db-migrate:
	@echo "Running Alembic migrations..."
	docker compose run --rm backend alembic upgrade head
	@echo "Migrations complete!"

# AI setup target
setup-ollama:
	@echo "Setting up Ollama..."
	@if command -v ollama >/dev/null 2>&1; then \
		echo "✓ Ollama is already installed"; \
	else \
		echo "Installing Ollama..."; \
		curl -fsSL https://ollama.com/install.sh | sh; \
	fi
	@echo ""
	@echo "Pulling mistral model (this may take a few minutes, ~4.1GB)..."
	ollama pull mistral
	@echo ""
	@echo "✓ Ollama setup complete!"
	@echo ""
	@echo "To start Ollama for Docker access, run:"
	@echo "  OLLAMA_HOST=0.0.0.0:11434 ollama serve"
	@echo ""
	@echo "Or add to your shell profile (~/.bashrc or ~/.zshrc):"
	@echo "  export OLLAMA_HOST=0.0.0.0:11434"

# Utility targets
clean:
	@echo "Removing all containers, volumes, and images..."
	@read -p "This will delete all Docker resources for this project. Continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose down -v --rmi all; \
		echo "Cleanup complete!"; \
	else \
		echo "Cleanup cancelled."; \
	fi
