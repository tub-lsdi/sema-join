from logging.config import fileConfig

import os
import sys

from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except Exception:
    pass

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()

db_user = os.getenv("APP_DB_USERNAME")
db_pass = os.getenv("APP_DB_PASSWORD")
db_host = os.getenv("APP_DB_HOST")
db_port = os.getenv("APP_DB_PORT")
db_name = os.getenv("APP_DB_DATABASE")

sqlalchemy_url = f"mysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
print(sqlalchemy_url)

config.set_main_option("sqlalchemy.url", sqlalchemy_url)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.persistence import Base
except Exception:
    from backend.persistence.base import Base

target_metadata = Base.metadata


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
