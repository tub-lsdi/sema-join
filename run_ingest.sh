#!/bin/bash

# Script to run corpus ingestion directly on host (outside Docker)
# This avoids Docker file mounting issues on macOS

set -e

echo "Running corpus ingestion on host..."

# Check if backend/corpus/data/tables.json exists
if [ ! -f "backend/corpus/data/tables.json" ]; then
    echo "Error: backend/corpus/data/tables.json not found"
    echo "Please ensure the corpus data file exists before running ingestion."
    exit 1
fi

# Remove old corpus.db if it exists
echo "Removing old corpus.db if it exists..."
rm -rf corpus.db

# Create temp directory if it doesn't exist
echo "Creating _temp directory..."
mkdir -p _temp

# Set environment variables for the ingestion script
export DB_PATH="corpus.db"
export DUCKDB_TEMP_DIRECTORY="_temp"

# Activate virtual environment and run the ingestion script
echo "Running ingestion script..."
cd backend
source .venv/bin/activate
python corpus/setup_db/01_ingest_corpus_parallel.py
deactivate
cd ..

echo ""
echo "✅ Corpus ingestion complete! Database created at: corpus.db"
echo ""
echo "You can now run 'make up' to start the Docker services."
