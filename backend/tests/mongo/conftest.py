from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import core.mongo_legacy as mongo_legacy_module
import services.order_service as order_service_module
from core.deployment import load_deployment_config
from dependencies.mongo_auth import get_current_user
from main import create_app
from tests.mongo_fake import FakeDB, make_user, seed_orderable_tea

_PROFESSIONAL_PRESET = (
    Path(__file__).resolve().parents[3] / "deploy" / "presets" / "professional.yaml"
)

def _build_v1_client(
    monkeypatch,
    fake_db: FakeDB,
    auth_user: dict[str, Any] | None,
    fastapi_app,
):
    monkeypatch.setattr(mongo_legacy_module, "db", fake_db)
    monkeypatch.setattr(order_service_module, "db", fake_db)
    monkeypatch.setenv("USE_DB_TRANSACTIONS", "false")

    if auth_user is not None:
        fastapi_app.dependency_overrides[get_current_user] = lambda: auth_user

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def orders_api_app():
    return create_app(load_deployment_config(_PROFESSIONAL_PRESET))

@pytest.fixture
def fake_db():
    return FakeDB()

@pytest.fixture
def client(monkeypatch, fake_db: FakeDB, orders_api_app):
    yield from _build_v1_client(monkeypatch, fake_db, make_user("admin"), orders_api_app)

@pytest.fixture
def client_no_auth(monkeypatch, fake_db: FakeDB, orders_api_app):
    yield from _build_v1_client(monkeypatch, fake_db, None, orders_api_app)

@pytest.fixture
def client_user(monkeypatch, fake_db: FakeDB, orders_api_app):
    yield from _build_v1_client(monkeypatch, fake_db, make_user("user"), orders_api_app)

@pytest.fixture
def client_guest(monkeypatch, fake_db: FakeDB, orders_api_app):
    yield from _build_v1_client(monkeypatch, fake_db, make_user("guest"), orders_api_app)

@pytest.fixture
def seeded_tea_id(fake_db: FakeDB) -> str:
    return seed_orderable_tea(fake_db, quantity=3)