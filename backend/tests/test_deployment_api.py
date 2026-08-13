from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from models.tenant import Tenant
from models.user import User
from routes.auth import router as product_auth_router
from routes.deployment import router as deployment_router

_PERSONAL_SIGNUP = {
    "slug": "sample-shop",
    "username": "owner1",
    "name": "Owner",
    "email": "owner@example.com",
    "password": "secretpass",
}

def _login(client: TestClient, *, slug: str, username: str = "owner1") -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "slug": slug,
            "username": username,
            "password": "secretpass",
        },
    )
    assert response.status_code == 200

import pytest

@pytest.fixture(autouse=True)
def stub_password_hashing(monkeypatch):
    def fake_hash(password: str) -> str:
        return f"hashed:{password}"

    def fake_verify(password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"

    monkeypatch.setattr("routes.auth.hash_password", fake_hash)
    monkeypatch.setattr("routes.auth.verify_password", fake_verify)

@pytest.fixture
def deployment_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        User.__table__.drop(bind=engine)
        Tenant.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def deployment_client(deployment_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")
    app.include_router(deployment_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield deployment_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_get_deployment_requires_authenticated_tenant_user(
    deployment_client: TestClient,
):
    response = deployment_client.get("/api/deployment")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_deployment_returns_current_tenant_personal_config(
    deployment_client: TestClient,
):
    signup = deployment_client.post("/api/auth/signup", json=_PERSONAL_SIGNUP)
    assert signup.status_code == 201
    _login(deployment_client, slug="sample-shop")

    response = deployment_client.get("/api/deployment")

    assert response.status_code == 200
    body = response.json()
    assert body["edition"] == "personal"
    assert body["locale"] == "zh-TW"
    assert body["modules"]["orders"] is False
    assert "pending_orders" not in body["dashboard_layout"]
    assert body["capabilities"] == [
        "manage_inventory",
        "view_catalog",
        "view_pricing",
    ]

def test_get_deployment_returns_current_tenant_professional_config(
    deployment_client: TestClient,
):
    signup = deployment_client.post(
        "/api/auth/signup",
        json={
            **_PERSONAL_SIGNUP,
            "slug": "pro-shop",
            "edition": "professional",
        },
    )
    assert signup.status_code == 201
    _login(deployment_client, slug="pro-shop")

    response = deployment_client.get("/api/deployment")

    assert response.status_code == 200
    body = response.json()
    assert body["edition"] == "professional"
    assert body["modules"]["orders"] is True
    assert body["modules"]["profit_analytics"] is True
    assert "pending_orders" in body["dashboard_layout"]
    assert body["capabilities"] == [
        "approve_orders",
        "manage_inventory",
        "view_catalog",
        "view_pricing",
        "view_profit",
    ]
