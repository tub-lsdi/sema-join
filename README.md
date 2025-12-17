# SEMA-JOIN

Semantic table joins using PMI-based matching.

**📚 [Full Documentation](https://tub-lsdi.github.io/sema-join-docs/)**

## Prerequisites

- Docker & docker-compose
- Python 3.10+ with uv
- Ollama (optional, for AI features)

## Quick Setup

1. **Clone repository**
```bash
git clone <repository-url>
cd sema-join
```

2. **Add corpus data**
   - Place your corpus JSON files in `corpus/data/` directory

3. **Install dependencies**
```bash
cd corpus
uv sync
cd ..
```

4. **Create `.env` file**
```bash
cp .env.example .env
# Then edit .env with your configuration (see example below)
```

5. **Ingest corpus data**
```bash
make ingest
```

6. **Build and start services**
```bash
make build
make up
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Optional - Setup Ollama (for AI features):**
```bash
make setup-ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

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
