# SEMA-JOIN

Semantic table joins using PMI-based matching.

**📚 [Full Documentation](https://tub-lsdi.github.io/sema-join-docs/docs/)**

## Prerequisites

- Docker & Docker Compose
- Python 3.10 or higher
- uv package manager for Python
- Ollama (optional, for AI features)

## Quick Setup

1. **Clone repository**
```bash
git clone https://github.com/tub-lsdi/sema-join.git
cd sema-join
```

2. **Create `.env` file**
```bash
cp .env.example .env
# Then edit .env with your configuration
```

3. **Install dependencies**
```bash
cd corpus
uv sync
cd ..
```
4.1 **Download pre-built databases**
If you want to ingest data from JSON files, proceed with step 4.2. If you already have a database, adding the path to it in the `.env` file is sufficient.
You may also download our pre-built databases from:

1. **Wiki Corpus**: https://tubcloud.tu-berlin.de/s/XYDeqCGcC25pWKg
2. **Git Tables Corpus**: https://tubcloud.tu-berlin.de/s/y7rYRZR74ECAjs3

The downloaded files are .zip archives. Extract them first, then place it at the location you specified in the `.env` file.
You can continure from step 6.

4.2 **Create data directory and add corpus data**

First, create the data directory:
```bash
mkdir -p corpus/data
```

You can use the Wikipedia Tables dataset ("A dataset of 1.6M Wikipedia Tables in JSON format") from:

📥 http://websail-fe.cs.northwestern.edu/TabEL/

Add corpus JSON files to the `corpus/data/` directory. 

The expected structure looks like:

```
# Example structure:
# corpus/data/tables.json
```


5. **Ingest corpus data**
```bash
make ingest
```

If you are using MacOS or Windows, ensure that the docker deamon is running before continuing.
6. **Build and start services**
```bash
make build
make up
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Go Service: http://localhost:8080

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
