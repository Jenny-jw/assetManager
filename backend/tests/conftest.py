from __future__ import annotations

import os

os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://ci:ci@localhost:5432/ci_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("USE_DB_TRANSACTIONS", "false")

from pathlib import Path
from typing import Any

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

import core.mongo_legacy as mongo_legacy_module
import main as app_module
import services.order_service as order_service_module
from core.deployment import load_deployment_config
from dependencies.mongo_auth import get_current_user
from main import app, create_app
from tests.mongo_fake import FakeDB

_PROFESSIONAL_PRESET = (
    Path(__file__).resolve().parents[2] / "deploy" / "presets" / "professional.yaml"
)

def _make_owner() -> dict[str, Any]:
    return {
        "id": str(ObjectId()),
        "role": "owner",
        "username": "owner1",
        "email": "owner@example.com",
        "name": "Owner",
        "is_active": True,
    }

def _build_owner_client(
    monkeypatch,
    fake_db: FakeDB,
    auth_user: dict[str, Any] | None,
    fastapi_app: FastAPI,
):
    monkeypatch.setattr(mongo_legacy_module, "db", fake_db)
    monkeypatch.setattr(order_service_module, "db", fake_db)
    monkeypatch.setenv("USE_DB_TRANSACTIONS", "false")

    if auth_user is not None:
        fastapi_app.dependency_overrides[get_current_user] = lambda: auth_user

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def skip_startup_postgres_ping(monkeypatch):
    monkeypatch.setattr(app_module, "ping_postgres", lambda: None)

@pytest.fixture
def fake_db():
    return FakeDB()

@pytest.fixture
def personal_app():
    return app

@pytest.fixture
def professional_app():
    return create_app(load_deployment_config(_PROFESSIONAL_PRESET))

@pytest.fixture
def client(personal_app: FastAPI):
    with TestClient(personal_app) as test_client:
        yield test_client

@pytest.fixture
def client_owner(monkeypatch, fake_db: FakeDB, personal_app: FastAPI):
    yield from _build_owner_client(monkeypatch, fake_db, _make_owner(), personal_app)

@pytest.fixture
def client_owner_professional(monkeypatch, fake_db: FakeDB, professional_app: FastAPI):
    yield from _build_owner_client(monkeypatch, fake_db, _make_owner(), professional_app)

@pytest.fixture
def client_no_auth(monkeypatch, fake_db: FakeDB, personal_app: FastAPI):
    yield from _build_owner_client(monkeypatch, fake_db, None, personal_app)