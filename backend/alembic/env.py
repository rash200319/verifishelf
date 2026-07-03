from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

sys.path.insert(0, str(BASE_DIR))
load_dotenv(PROJECT_ROOT / ".env")

config = context.config


def build_database_url() -> str:
    existing_url = os.getenv("ALEMBIC_DATABASE_URL")
    if existing_url:
        return existing_url

    root_password = quote_plus(os.getenv("MYSQL_ROOT_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3307")
    database_name = os.getenv("MYSQL_DB", "verifishelf")

    return f"mysql+pymysql://root:{root_password}@{host}:{port}/{database_name}"


config.set_main_option("sqlalchemy.url", build_database_url().replace("%", "%%"))

target_metadata = None


def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
