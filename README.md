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
- Python 3.13+
- uv (Python package manager)
- Node.js 20+ and npm
- Ollama 
- Mistral model (via Ollama: `ollama pull mistral`)

## 🚀 Quick Start (Recommended)

We provide a convenient management script for easy setup and running:

```bash
# Make the script executable (first time only)
chmod +x sema-join.sh

# Show help
./sema-join.sh
./sema-join.sh help

# Quick Start:
./sema-join.sh install all        # 1. Install all dependencies
./sema-join.sh db                  # 2. Setup database
./sema-join.sh ai setup            # 3. Setup AI (Ollama + Mistral)
./sema-join.sh ai serve            # 4. Start Ollama service
./sema-join.sh run                 # 5. Run both servers
```

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
./sema-join.sh db                  # Initialize database
./sema-join.sh db --large          # Initialize database with scripts for large corpora
./sema-join.sh status              # Check project status
./sema-join.sh help                # Show help

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