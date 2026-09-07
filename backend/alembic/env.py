"""Alembic environment — async SQLAlchemy 2.0 + asyncpg.

Reads DATABASE_URL from the app's Settings so the same env-var used by the
FastAPI app drives migrations too.  No credentials in alembic.ini.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── load app config & metadata ────────────────────────────────────────────────
# Import all models so every table is registered on Base.metadata before
# autogenerate compares it against the database.
import app.models  # noqa: F401 — side-effect: registers all ORM classes
from app.core.config import settings
from app.core.db import Base

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Inject the app DATABASE_URL so alembic.ini can stay credential-free.
# asyncpg uses "postgresql+asyncpg://…" which works fine with async_engine_from_config.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── offline migrations ─────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection.
    Useful for generating a SQL script to review before applying.
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


# ── online migrations (async) ──────────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
