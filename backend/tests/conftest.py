from __future__ import annotations

import os

os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://ci:ci@localhost:5432/ci_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("USE_DB_TRANSACTIONS", "false")

import pytest

import main as app_module

@pytest.fixture(autouse=True)
def skip_startup_postgres_ping(monkeypatch):
    monkeypatch.setattr(app_module, "ping_postgres", lambda: None)