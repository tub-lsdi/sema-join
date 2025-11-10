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

# Application Database Configuration
APP_DB_CONTAINER_NAME=sema_app_db
APP_DB_HOST=localhost
APP_DB_PORT=3306
APP_DB_DATABASE=sema_app_db
APP_DB_USERNAME=your_username
APP_DB_PASSWORD=your_password
APP_DB_ROOT_PASSWORD=your_root_password
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
The temporary directory is used for intermediate data storage during processing. Depending on the size of your corpus, ensure this directory has sufficient space. This can me a multiple of the original corpus size.
Make sure there is enough free disk space in the specified directory. This can be on a separate volume.
Also note, that read and write speeds of the disk can impact performance.

### Batch Processing

Adjust batch sizes for corpus ingestion:

```bash
CELL_BATCH_SIZE=1000000
TABLE_BATCH_SIZE=50000
```

### Application Database Configuration

Configure the application database connection (used for storing join history):

```bash
APP_DB_CONTAINER_NAME=sema_app_db
APP_DB_HOST=localhost
APP_DB_PORT=3306
APP_DB_DATABASE=sema_app_db
APP_DB_USERNAME=your_username
APP_DB_PASSWORD=your_password
APP_DB_ROOT_PASSWORD=your_root_password
```

- `APP_DB_CONTAINER_NAME`: Container name for the app database (e.g., `sema_app_db`)
- `APP_DB_HOST`: Host for the app database (e.g., `localhost`)
- `APP_DB_PORT`: Port for the app database (e.g., `3306` for MySQL/MariaDB)
- `APP_DB_DATABASE`: Name of the app database (e.g., `sema_app_db`)
- `APP_DB_USERNAME`: Username for the app database
- `APP_DB_PASSWORD`: Password for the app database user
- `APP_DB_ROOT_PASSWORD`: Root password for the app database

**Note:** These variables are required for the application database functionality. Adjust the values according to your database setup.

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

# Application Database Configuration
APP_DB_CONTAINER_NAME=sema_app_db
APP_DB_HOST=localhost
APP_DB_PORT=3306
APP_DB_DATABASE=sema_app_db
APP_DB_USERNAME=your_username
APP_DB_PASSWORD=your_password
APP_DB_ROOT_PASSWORD=your_root_password

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
