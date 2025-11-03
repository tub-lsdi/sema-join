#!/bin/bash
# Script to run the Semantic Join API server

echo "Starting Semantic Join API server..."
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

cd "$(dirname "$0")/.." || exit

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

