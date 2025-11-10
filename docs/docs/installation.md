---
sidebar_position: 3
---

# Installation

This guide walks you through installing Project SEMA-JOIN on your system.

## System Requirements

Ensure your system meets these requirements:

- Python 3.13 or higher
- Node.js 20 or higher
- uv package manager for Python
- At least 4GB RAM
- 2GB free disk space

## Installation Steps

### Step 1: Clone the Repository

Download the Project SEMA-JOIN source code to your local machine:

```bash
git clone https://github.com/tub-lsdi/sema-join.git
cd sema-join
```

### Step 2: Make Script Executable

Make the management script executable:

```bash
chmod +x sema-join.sh
```

### Step 3: Configure Environment

Create a `.env` file in the project root with the required configuration. See the [Environment Setup](./environment-setup.md) guide for details.

At minimum, create `.env` with:

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

### Step 4: Install All Dependencies

Install both backend and frontend dependencies:

```bash
./sema-join.sh install all
```

This will:
- Install Python backend dependencies using uv
- Install Node.js frontend dependencies
- Set up the virtual environment

### Step 5: Start Docker Services

Start the application database using Docker Compose:

```bash
./sema-join.sh docker run
```

This will build and start the Docker containers defined in `docker-compose.yml`.

### Step 6: Initialize Application Database

Run Alembic migrations to set up the application database schema:

```bash
./sema-join.sh app_db
```

This will create the necessary tables for storing join history.

### Step 7: Install AI Service (Optional)

The AI-powered column matching feature requires Ollama with the Mistral model:

```bash
./sema-join.sh ai setup
```

This will install Ollama and download the Mistral model.

### Step 8: Verify Installation

Check that all components are properly installed:

```bash
./sema-join.sh status
```

## Manual Installation

If you prefer to install components individually:

### Backend Setup

Install Python dependencies:

```bash
uv sync --extra backend
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Or use uv run to execute commands without activating:

```bash
uv run <command>
```

### Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

### AI Setup

Install Ollama for your operating system:

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

Pull the Mistral model:

```bash
ollama pull mistral
```

## Troubleshooting

**Port Conflicts**
The backend uses port 8000 and frontend uses port 3000. Ensure these ports are available.

**AI Features Not Working**
The AI-powered column matching requires Ollama to be running on port 11434. Start Ollama with `ollama serve` or use `./sema-join.sh ai serve`.

## Next Steps

After installation, proceed to corpus ingestion to build the semantic join database.
