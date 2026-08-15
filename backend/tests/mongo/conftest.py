from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.deployment import get_deployment, load_professional_preset
from core.errors import register_exception_handlers
import core.mongo_legacy as mongo_legacy_module
from dependencies.mongo_auth import get_current_user
from modules.orders.mongo_routes import router as mongo_orders_router
import services.order_service as order_service_module
from tests.mongo_fake import FakeDB, make_user, seed_orderable_tea

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
    app = FastAPI()
    register_exception_handlers(app)
    professional = load_professional_preset()
    app.dependency_overrides[get_deployment] = lambda: professional
    app.include_router(mongo_orders_router, prefix="/api")
    return app

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