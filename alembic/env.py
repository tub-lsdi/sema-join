from logging.config import fileConfig

import os
import sys

from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# If the project uses PyMySQL (mysql+pymysql) but Alembic/config expects
# the MySQLdb DBAPI, allow pymysql to register itself as MySQLdb so
# engine_from_config() can import MySQLdb. This avoids requiring
# mysqlclient to be installed when using PyMySQL.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except Exception:
    # If pymysql isn't installed, let the original error surface when
    # Alembic actually tries to create the engine (so the user can
    # install the appropriate DBAPI).
    pass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()

# Read DB connection pieces from environment
db_user = os.getenv("APP_DB_USERNAME")
db_pass = os.getenv("APP_DB_PASSWORD")
db_host = os.getenv("APP_DB_HOST")
db_port = os.getenv("APP_DB_PORT")
db_name = os.getenv("APP_DB_DATABASE")

sqlalchemy_url = f"mysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
print(sqlalchemy_url)

config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# ensure the project root is on PYTHONPATH so we can import models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# add your model's MetaData object here
# for 'autogenerate' support
# import the project's Base so Alembic can reflect models
try:
    # package `backend.persistence` exposes `Base` in __init__.py
    from backend.persistence import Base
except Exception:
    # fallback: import directly from module
    from backend.persistence.base import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
