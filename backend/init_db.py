from sqlalchemy import text
from loguru import logger


def init_database_tables(engine) -> None:
    """Create database tables automatically if they don't exist."""

    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text(
            "SELECT COUNT(*) as count FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name IN ('table_entry', 'join_history', 'uploaded_table')"
        ))
        existing_tables_count = result.fetchone()[0]

        if existing_tables_count == 3:
            logger.info("Database tables already exist. Skipping initialization.")
            return

        logger.info("Database tables not found. Creating tables automatically...")

        # Create table_entry table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS table_entry (
                id INT AUTO_INCREMENT PRIMARY KEY,
                body LONGTEXT NOT NULL,
                columns JSON NOT NULL
            )
        """))
        logger.info("Created table: table_entry")

        # Create join_history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS join_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                list_r_entry_id INT NOT NULL,
                list_s_entry_id INT NOT NULL,
                bridge_table_entry_id INT NOT NULL,
                result_entry_id INT NOT NULL,
                r_join_col VARCHAR(64) NOT NULL,
                s_join_col VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bridge_table_entry_id) REFERENCES table_entry(id),
                FOREIGN KEY (list_r_entry_id) REFERENCES table_entry(id),
                FOREIGN KEY (list_s_entry_id) REFERENCES table_entry(id),
                FOREIGN KEY (result_entry_id) REFERENCES table_entry(id)
            )
        """))
        logger.info("Created table: join_history")

        # Create uploaded_table table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS uploaded_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                body LONGTEXT NOT NULL,
                columns JSON NOT NULL
            )
        """))
        logger.info("Created table: uploaded_table")

        conn.commit()
        logger.info("Database initialization complete! All tables created successfully.")
