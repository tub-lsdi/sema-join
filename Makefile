.PHONY: up down build logs logs-backend logs-frontend migrate migrate-down migrate-create ingest test clean restart

# Start all services
up:
	docker compose up -d

up-frontend:
	docker compose up -d frontend

up-backend:
	docker compose up -d backend

# Stop all services
down:
	docker compose down

# Build all images
build:
	docker compose build

# View logs from all services
logs:
	docker compose logs -f

# View backend logs only
logs-backend:
	docker compose logs -f backend

# View frontend logs only
logs-frontend:
	docker compose logs -f frontend

# Run Alembic migrations
migrate:
	docker compose exec backend sh -c "cd backend && uv run alembic upgrade head"

# Rollback one migration
migrate-down:
	docker compose exec backend sh -c "cd backend && uv run alembic downgrade -1"

# Create new migration
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='migration message'"; \
		exit 1; \
	fi
	docker compose exec backend sh -c "cd backend && uv run alembic revision --autogenerate -m '$(MSG)'"

# Run ingest_parallel script
ingest:
	docker compose exec backend uv run python backend/corpus/setup_db/01_ingest_corpus_parallel.py

# Run tests
test:
	docker compose exec backend uv run python -m unittest discover -s backend/tests -p "test_*.py" -v

# Clean up containers and volumes
clean:
	docker compose down -v

# Restart all services
restart: down up


