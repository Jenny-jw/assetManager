from __future__ import annotations

from collections.abc import Generator
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import core.env  # noqa: F401

Base = declarative_base()
_session_factory: sessionmaker[Session] | None = None

_engine: Engine | None = None

def _require_postgres_url() -> str:
    url = os.getenv("POSTGRES_URL", "").strip()
    if not url:
        raise RuntimeError(
            "POSTGRES_URL is required on the product branch (no MONGO_URI fallback)"
        )
    return url

def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(_require_postgres_url(), pool_pre_ping=True)
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _engine

def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory

def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()

def ping_postgres() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))

def reset_db_state_for_tests() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
