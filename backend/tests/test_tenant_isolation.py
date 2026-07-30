from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from models.stock import Stock
from models.tenant import Tenant
from models.user import User
from routes.auth import router as product_auth_router
from routes.deployment import router as deployment_router
from routes.stock import router as stock_router

_STOCK_PAYLOAD = {
    "name": "Tenant Tea",
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
def isolation_session(monkeypatch) -> Generator[Session, None, None]:
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
def isolation_app(isolation_session: Session) -> Generator[FastAPI, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")
    app.include_router(stock_router, prefix="/api")
    app.include_router(deployment_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield isolation_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()

def _client(app: FastAPI) -> TestClient:
    return TestClient(app)

def _signup_login(client: TestClient, *, slug: str) -> str:
    signup = client.post(
        "/api/auth/signup",
        json={
            "slug": slug,
            "username": "owner1",
            "name": "Owner",
            "email": f"{slug}@example.com",
            "password": "secretpass",
            "edition": "personal",
        },
    )
    assert signup.status_code == 201
    tenant_id = signup.json()["tenant_id"]
    login = client.post(
        "/api/auth/login",
        json={"slug": slug, "username": "owner1", "password": "secretpass"},
    )
    assert login.status_code == 200
    return tenant_id

def test_stock_list_is_isolated_between_tenants(isolation_app: FastAPI):
    client_a = _client(isolation_app)
    client_b = _client(isolation_app)

    _signup_login(client_a, slug="shop-a")
    created = client_a.post("/api/stock/", json=_STOCK_PAYLOAD)
    assert created.status_code == 201
    stock_id = created.json()["id"]

    listed_a = client_a.get("/api/stock/")
    assert listed_a.status_code == 200
    assert listed_a.json()["total"] == 1
    assert listed_a.json()["data"][0]["id"] == stock_id

    _signup_login(client_b, slug="shop-b")
    listed_b = client_b.get("/api/stock/")
    assert listed_b.status_code == 200
    assert listed_b.json()["total"] == 0
    assert listed_b.json()["data"] == []

def test_stock_get_update_delete_are_isolated_between_tenants(isolation_app: FastAPI):
    client_a = _client(isolation_app)
    client_b = _client(isolation_app)

    _signup_login(client_a, slug="alpha-shop")
    created = client_a.post(
        "/api/stock/",
        json={**_STOCK_PAYLOAD, "name": "Alpha Only"},
    )
    assert created.status_code == 201
    stock_id = created.json()["id"]

    _signup_login(client_b, slug="beta-shop")
    assert client_b.get(f"/api/stock/{stock_id}").status_code == 404
    assert (
        client_b.patch(f"/api/stock/{stock_id}", json={"name": "Hijacked"}).status_code
        == 404
    )
    assert client_b.delete(f"/api/stock/{stock_id}").status_code == 404

    # Tenant A still owns the row.
    still_there = client_a.get(f"/api/stock/{stock_id}")
    assert still_there.status_code == 200
    assert still_there.json()["name"] == "Alpha Only"

def test_deployment_config_is_isolated_between_tenants(isolation_app: FastAPI):
    client_a = _client(isolation_app)
    client_b = _client(isolation_app)

    _signup_login(client_a, slug="personal-a")
    personal = client_a.get("/api/deployment")
    assert personal.status_code == 200
    assert personal.json()["edition"] == "personal"
    assert personal.json()["modules"]["orders"] is False

    signup_b = client_b.post(
        "/api/auth/signup",
        json={
            "slug": "pro-b",
            "username": "owner1",
            "name": "Pro Owner",
            "password": "secretpass",
            "edition": "professional",
        },
    )
    assert signup_b.status_code == 201
    login_b = client_b.post(
        "/api/auth/login",
        json={"slug": "pro-b", "username": "owner1", "password": "secretpass"},
    )
    assert login_b.status_code == 200

    professional = client_b.get("/api/deployment")
    assert professional.status_code == 200
    assert professional.json()["edition"] == "professional"
    assert professional.json()["modules"]["orders"] is True

    # Tenant A remains on personal config.
    personal_again = client_a.get("/api/deployment")
    assert personal_again.status_code == 200
    assert personal_again.json()["edition"] == "personal"
    assert personal_again.json()["modules"]["orders"] is False

def test_same_username_can_exist_in_different_tenants(isolation_app: FastAPI):
    client_a = _client(isolation_app)
    client_b = _client(isolation_app)

    tenant_a = _signup_login(client_a, slug="dup-a")
    tenant_b = _signup_login(client_b, slug="dup-b")

    assert tenant_a != tenant_b
    assert client_a.get("/api/stock/").status_code == 200
    assert client_b.get("/api/stock/").status_code == 200
