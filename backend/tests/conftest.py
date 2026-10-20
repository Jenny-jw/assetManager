from __future__ import annotations

import os

os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://ci:ci@localhost:5432/ci_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient
import pytest

import main as app_module
from main import app

@pytest.fixture(autouse=True)
def skip_startup_postgres_ping(monkeypatch):
    monkeypatch.setattr(app_module, "ping_postgres", lambda: None)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
