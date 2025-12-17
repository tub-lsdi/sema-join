from typing import Tuple
import os
import urllib.parse

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def create_mysql_engine_and_sessionmaker() -> Tuple[object, sessionmaker]:
    """Create a SQLAlchemy engine and sessionmaker for the application DB.

    Reads connection parameters from environment variables.
    Automatically creates the database if it doesn't exist.
    """
    db_host = os.getenv("APP_DB_HOST", "localhost")
    db_port = os.getenv("APP_DB_PORT", "3306")
    db_name = os.getenv("APP_DB_DATABASE", "sema_app_db")
    db_user = os.getenv("APP_DB_USERNAME", "root")
    db_password = os.getenv("APP_DB_PASSWORD", "")

    db_user_enc = urllib.parse.quote_plus(db_user)
    db_password_enc = urllib.parse.quote_plus(db_password)

    logger.info(
        f"Connecting to MySQL at {db_host}:{db_port} as user '{db_user}'")

    # First, connect without database to create it if needed
    base_url = f"mysql+pymysql://{db_user_enc}:{db_password_enc}@{db_host}:{db_port}"
    base_engine = create_engine(base_url, pool_pre_ping=True)

    try:
        with base_engine.connect() as conn:
            # Create database if it doesn't exist
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
            conn.commit()
            logger.info(f"Database '{db_name}' is ready")
    except Exception as e:
        logger.error(f"Failed to create/check database: {e}")
        raise
    finally:
        base_engine.dispose()

    # Now connect to the specific database
    mysql_url = f"{base_url}/{db_name}"
    engine = create_engine(mysql_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, future=True)

    return engine, Session


def init_app_db(app) -> None:
    """Attach engine and sessionmaker to FastAPI app.state."""
    engine, Session = create_mysql_engine_and_sessionmaker()
    app.state.app_db_engine = engine
    app.state.app_db_sessionmaker = Session


def shutdown_app_db(app) -> None:
    """Dispose engine stored on the app.state if present."""
    if hasattr(app.state, "app_db_engine"):
        try:
            app.state.app_db_engine.dispose()
        except Exception as e:
            logger.warning(f"Error disposing app database engine: {e}")
