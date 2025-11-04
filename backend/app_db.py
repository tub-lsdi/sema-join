"""Application database (MySQL) helpers using SQLAlchemy.

This module creates and exposes helpers to initialize and shutdown the
SQLAlchemy engine and sessionmaker for the application's MySQL database.
"""

from typing import Tuple
import os
import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_mysql_engine_and_sessionmaker() -> Tuple[object, sessionmaker]:
    """Create a SQLAlchemy engine and sessionmaker for the application DB.

    Reads connection parameters from environment variables and URL-encodes
    username/password to be safe with special characters.
    """
    db_host = os.getenv("APP_DB_HOST", "localhost")
    db_port = os.getenv("APP_DB_PORT", "3306")
    db_name = os.getenv("APP_DB_DATABASE", "sema_app_db")
    db_user = os.getenv("APP_DB_USERNAME", "semajoin")
    db_password = os.getenv("APP_DB_PASSWORD", "semajoin")

    db_user_enc = urllib.parse.quote_plus(db_user)
    db_password_enc = urllib.parse.quote_plus(db_password)

    # Use the pymysql driver; requires `pymysql` to be installed in the environment.
    mysql_url = (
        f"mysql+pymysql://{db_user_enc}:{db_password_enc}@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(mysql_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, future=True)

    return engine, Session


def init_app_db(app) -> None:
    """Attach engine and sessionmaker to FastAPI app.state.

    After calling this, `app.state.app_db_engine` and
    `app.state.app_db_sessionmaker` will be available.
    """
    engine, Session = create_mysql_engine_and_sessionmaker()
    app.state.app_db_engine = engine
    app.state.app_db_sessionmaker = Session


def shutdown_app_db(app) -> None:
    """Dispose engine stored on the app.state if present."""
    if hasattr(app.state, "app_db_engine"):
        try:
            app.state.app_db_engine.dispose()
        except Exception:
            # swallow exceptions during shutdown
            pass
