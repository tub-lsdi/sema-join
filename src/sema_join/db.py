import duckdb
import os

## go up three levels to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data/db/sema_join_test.db")

def get_db_connection():
    """Returns a connection to the project's DuckDB database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return duckdb.connect(database=DB_PATH)