# Database Setup Scripts

This directory contains scripts to set up the semantic join database.

## Scripts

### 01_ingest_corpus.py
**Purpose**: Ingest corpus data from JSON files into the database

**What it does**:
- Reads all `.json` files from `corpus/data/`
- Extracts tables and normalizes values
- Creates `tables_meta` and `cells` tables
- Stores table metadata and cell values in the database

**Usage**:
```bash
# From project root
python backend/corpus/setup_db/01_ingest_corpus.py
```

### 02_calculate_stats.py
**Purpose**: Calculate PMI statistics for semantic joins

**What it does**:
- Computes value frequencies (`values_index` table)
- Calculates co-occurrence statistics (`row_cooccurrences` table)
- Computes PMI scores (`pmi_scores` table)
- Creates indexes for fast lookups

**Usage**:
```bash
# From project root
python backend/corpus/setup_db/02_calculate_stats.py
```

**Note**: Must run `01_ingest_corpus.py` first!

## Automated Setup

Instead of running these scripts manually, use the master setup script:

```bash
./backend/setup_database.sh
```

This runs both scripts in the correct order with proper error handling.

## Database Location

The database is created at: `db.py` (project root)

This is managed by `backend/services/__init__.py`'s `get_db_connection()` function which automatically:
- Calculates the project root directory
- Connects to the database at the correct location

## Technical Details

### Path Resolution

Both scripts use relative path imports to ensure they work regardless of where they're called from:

```python
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# Get corpus data directory
INPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data"
)
```

This ensures:
- The `sema_join` package is importable
- Corpus data is read from the correct location
- Database is created in the project root

### Database Schema

**tables_meta**
- `table_id`: Unique table identifier
- `table_hash`: Hash for deduplication
- `source_file`: Original JSON file path
- `url`: Source URL from JSON

**cells**
- `table_id`: Foreign key to tables_meta
- `row_id`: Row number within table
- `col_id`: Column number within table
- `value`: Normalized cell value

**values_index**
- `value`: Normalized value
- `num_tables`: Number of tables containing this value

**row_cooccurrences**
- `v1`, `v2`: Value pair (ordered)
- `num_tables`: Number of tables where they co-occur

**pmi_scores**
- `v1`, `v2`: Value pair (ordered)
- `num_tables_pair`: Co-occurrence count
- `num_tables_v1`, `num_tables_v2`: Individual counts
- `pmi`: Pointwise Mutual Information score

### Performance Considerations

- **Batch Processing**: Cells are inserted in batches of 50,000 for efficiency
- **Deduplication**: Table hashes prevent duplicate ingestion
- **Indexes**: Automatic indexing on frequently queried columns
- **Pruning**: Values/pairs appearing in <2 tables are filtered out

## Troubleshooting

### Import Errors
Ensure you're running from the project root and the `sema_join` package is installed:
```bash
pip install -e .
```

### No JSON Files Found
Check that JSON files exist in `backend/corpus/data/`:
```bash
ls backend/corpus/data/*.json
```

### Database Connection Issues
The database will be automatically created at `db.py` in the project root. If you see errors, check:
- Write permissions in the project directory
- Disk space availability

### Path Issues
If scripts can't find the corpus data, verify you're running from the project root:
```bash
pwd  # Should show: /path/to/sema-join
```

## Development

### Modifying Ingestion Logic
Edit `01_ingest_corpus.py` to change:
- Normalization strategy
- Batch size
- Table filtering logic

### Modifying Statistics
Edit `02_calculate_stats.py` to change:
- PMI calculation formula
- Pruning thresholds (currently min 2 occurrences)
- Index creation

### Adding New Statistics
Add new queries in `02_calculate_stats.py` to create additional tables for your custom metrics.

