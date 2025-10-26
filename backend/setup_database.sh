#!/bin/bash
# Database Setup Script for Semantic Join Backend
# This script initializes the database by:
# 1. Ingesting corpus data from JSON files
# 2. Calculating PMI statistics

set -e 

echo "========================================"
echo "Semantic Join - Database Setup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"
echo -e "${BLUE}Backend directory: ${SCRIPT_DIR}${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if corpus data directory exists
if [ ! -d "$SCRIPT_DIR/corpus/data" ]; then
    echo -e "${RED}❌ Error: corpus data directory not found at $SCRIPT_DIR/corpus/data${NC}"
    echo "Please ensure the corpus data is available."
    exit 1
fi

# Count JSON files in corpus data
JSON_COUNT=$(find "$SCRIPT_DIR/corpus/data" -name "*.json" | wc -l)
if [ "$JSON_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Error: No JSON files found in corpus directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found ${JSON_COUNT} JSON file(s) in corpus directory${NC}"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Error: Python is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1/2: Ingesting corpus data...${NC}"
echo "This may take a few minutes depending on corpus size."
echo ""

python "$SCRIPT_DIR/corpus/setup_db/01_ingest_corpus.py"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Step 1 complete: Corpus data ingested successfully${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Error: Corpus ingestion failed${NC}"
    exit 1
fi

echo -e "${BLUE}Step 2/2: Calculating PMI statistics...${NC}"
echo "This will compute value counts, co-occurrences, and PMI scores."
echo ""

python "$SCRIPT_DIR/corpus/setup_db/02_calculate_stats.py"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Step 2 complete: Statistics calculated successfully${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Error: Statistics calculation failed${NC}"
    exit 1
fi

# Check if database file was created
if [ -f "$PROJECT_ROOT/db.py" ]; then
    DB_SIZE=$(du -h "$PROJECT_ROOT/db.py" | cut -f1)
    echo -e "${GREEN}✅ Database created: db.py (${DB_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Database file not found at expected location${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✨ Database setup complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Start the API server:"
echo "     ./backend/run_server.sh"
echo ""
echo "  2. Test the API:"
echo "     python backend/example_client.py"
echo ""
echo "  3. View API docs:"
echo "     http://localhost:8000/docs"
echo ""

