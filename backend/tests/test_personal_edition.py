from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.capabilities import Capability, resolve_capabilities
from core.dashboard_widgets import effective_dashboard_layout
from core.db import get_db
from core.deployment import deployment_from_tenant, load_personal_preset
from models.stock import Stock
from models.tenant import Tenant
from models.user import User
from modules.inventory import router as stock_router
from modules.orders import router as orders_router
from routes.auth import router as product_auth_router
from routes.deployment import router as deployment_router

_PERSONAL_SIGNUP = {
    "slug": "personal-tea",
    "username": "owner1",
    "name": "Owner",
    "email": "owner@example.com",
    "password": "secretpass",
}

_STOCK_PAYLOAD = {
    "name": "Alishan Oolong",
    "genre": "Oolong",
    "origin": "Alishan",
    "weight_grams": 75,
    "quantity": 2,
    "price_per_jin": 1200,
}

@pytest.fixture(autouse=True)
def stub_password_hashing(monkeypatch):
    def fake_hash(password: str) -> str:
        return f"hashed:{password}"

    def fake_verify(password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"

    monkeypatch.setattr("routes.auth.hash_password", fake_hash)
    monkeypatch.setattr("routes.auth.verify_password", fake_verify)

@pytest.fixture
def personal_session(monkeypatch) -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    Stock.__table__.create(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    monkeypatch.setattr(
        "dependencies.deployment.get_session_factory",
        lambda: session_factory,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Stock.__table__.drop(bind=engine)
        User.__table__.drop(bind=engine)
        Tenant.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def personal_client(personal_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")
    app.include_router(deployment_router, prefix="/api")
    app.include_router(stock_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield personal_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def _signup_and_login(client: TestClient, *, slug: str = "personal-tea") -> None:
    signup = client.post(
        "/api/auth/signup",
        json={**_PERSONAL_SIGNUP, "slug": slug},
    )
    assert signup.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"slug": slug, "username": "owner1", "password": "secretpass"},
    )
    assert login.status_code == 200

def test_personal_signup_applies_personal_preset(
    personal_client: TestClient,
    personal_session: Session,
):
    _signup_and_login(personal_client)

    tenant = personal_session.scalar(
        select(Tenant).where(Tenant.slug == "personal-tea")
    )
    assert tenant is not None

    preset = load_personal_preset()
    assert tenant.edition == preset.edition.value
    assert tenant.locale == preset.locale.value
    assert tenant.modules == preset.modules.model_dump()
    assert tenant.dashboard_layout == preset.dashboard_layout
    assert tenant.modules["orders"] is False
    assert "pending_orders" not in tenant.dashboard_layout

def test_personal_owner_capabilities_from_tenant_deployment(
    personal_client: TestClient,
    personal_session: Session,
):
    _signup_and_login(personal_client)

    tenant = personal_session.scalar(
        select(Tenant).where(Tenant.slug == "personal-tea")
    )
    assert tenant is not None

    deployment = deployment_from_tenant(tenant)
    owner = {"id": "1", "role": "owner"}
    caps = resolve_capabilities(owner, deployment)

    assert Capability.manage_inventory in caps
    assert Capability.view_pricing in caps
    assert Capability.approve_orders not in caps
    assert Capability.view_profit not in caps

def test_personal_deployment_api_returns_orders_off_and_personal_widgets(
    personal_client: TestClient,
):
    _signup_and_login(personal_client)

    response = personal_client.get("/api/deployment")

    assert response.status_code == 200
    body = response.json()
    assert body["edition"] == "personal"
    assert body["modules"]["orders"] is False
    assert body["modules"]["profit_analytics"] is False
    assert body["dashboard_layout"] == [
        "summary",
        "origin",
        "genre",
        "recent_assets",
    ]
    assert "pending_orders" not in body["dashboard_layout"]
    assert body["capabilities"] == [
        "manage_inventory",
        "view_catalog",
        "view_pricing",
    ]
    assert "approve_orders" not in body["capabilities"]
    assert "view_profit" not in body["capabilities"]

def test_personal_effective_dashboard_layout_excludes_order_widgets(
    personal_client: TestClient,
    personal_session: Session,
):
    _signup_and_login(personal_client)

    tenant = personal_session.scalar(
        select(Tenant).where(Tenant.slug == "personal-tea")
    )
    assert tenant is not None

    layout = effective_dashboard_layout(deployment_from_tenant(tenant))
    assert layout == ["summary", "origin", "genre", "recent_assets"]
    assert "pending_orders" not in layout

def test_personal_tenant_orders_endpoints_return_module_disabled(
    personal_client: TestClient,
):
    _signup_and_login(personal_client)

    list_response = personal_client.get("/api/orders/")
    assert list_response.status_code == 403
    assert list_response.json()["detail"] == "module_disabled"

    create_response = personal_client.post(
        "/api/orders/",
        json={"items": [{"tea_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}]},
    )
    assert create_response.status_code == 403
    assert create_response.json()["detail"] == "module_disabled"

def test_personal_tenant_stock_api_supports_owner_crud(personal_client: TestClient):
    _signup_and_login(personal_client)

    empty_list = personal_client.get("/api/stock/")
    assert empty_list.status_code == 200
    assert empty_list.json()["data"] == []

    created = personal_client.post("/api/stock/", json=_STOCK_PAYLOAD)
    assert created.status_code == 201
    stock_id = created.json()["id"]
    assert created.json()["name"] == "Alishan Oolong"

    fetched = personal_client.get(f"/api/stock/{stock_id}")
    assert fetched.status_code == 200
    assert fetched.json()["quantity"] == 2

    patched = personal_client.patch(
        f"/api/stock/{stock_id}",
        json={"name": "Renamed Oolong", "quantity": 1},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Renamed Oolong"

    deleted = personal_client.delete(f"/api/stock/{stock_id}")
    assert deleted.status_code == 200
    assert personal_client.get(f"/api/stock/{stock_id}").status_code == 404
