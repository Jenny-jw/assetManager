from __future__ import annotations

import os
from logging.config import fileConfig

import core.env  # noqa: F401 — repo-root .env
from alembic import context
from sqlalchemy import engine_from_config, pool

import models.product  # noqa: F401 — registers ORM tables when added (P0-6)
from core.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _require_postgres_url() -> str:
    url = os.getenv("POSTGRES_URL", "").strip()
    if not url:
        raise RuntimeError(
            "POSTGRES_URL is required for Alembic (set in repo-root .env or shell)"
        )
    return url

def run_migrations_offline() -> None:
    context.configure(
        url=_require_postgres_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _require_postgres_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()