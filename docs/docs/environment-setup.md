---
sidebar_position: 2
---

# Environment Setup

Before using Project SEMA-JOIN, you must create a `.env` file in the project root. The management script requires this file to function.

## Creating the Configuration File

Create a `.env` file in the project root:

```bash
touch .env
```

Open the file in your text editor and add the required configuration.

## Required Configuration

At minimum, your `.env` file should contain:

```bash
DB_PATH=corpus.db
LOG_LEVEL=DEBUG
```

## Available Settings

### Database Path

Specify where the corpus database will be stored:

```bash
DB_PATH=corpus.db
```

This is the name of the database file that will be created in the project root.

### Logging Level

Control the verbosity of log output:

```bash
LOG_LEVEL=DEBUG
```

Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### DuckDB Settings

Configure DuckDB memory and temporary directory:

```bash
DUCKDB_MEMORY_LIMIT=10GB
DUCKDB_TEMP_DIRECTORY=./_temp
```

These settings control DuckDB's performance characteristics.

### Batch Processing

Adjust batch sizes for corpus ingestion:

```bash
CELL_BATCH_SIZE=1000000
TABLE_BATCH_SIZE=50000
```

### Ollama AI Configuration

Configure the Ollama service for AI-powered column matching:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=60
```

**Note:** If these variables are not set in your `.env` file, the system will use the default values shown above.

## Complete Example

A complete `.env` file with all common settings:

```bash
# Database Configuration
DB_PATH=corpus.db

# Logging
LOG_LEVEL=DEBUG

# DuckDB Performance
DUCKDB_MEMORY_LIMIT=10GB
DUCKDB_TEMP_DIRECTORY=./_temp

# Batch Processing
CELL_BATCH_SIZE=1000000
TABLE_BATCH_SIZE=50000

# Ollama AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=60
```

## Important Notes

**File is Required**  
The `.env` file must exist before running any `./sema-join.sh` commands. The script will fail if this file is missing.

## Verifying Configuration

After creating your `.env` file, verify it works:

```bash
./sema-join.sh status
```

This will check your configuration and show the status of all components.

## Next Steps

With your environment configured, proceed to installation to set up all dependencies.
