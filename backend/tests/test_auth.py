from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.deployment import load_personal_preset, load_professional_preset
from models.tenant import Tenant
from models.user import User
from routes.auth import router as product_auth_router

_SIGNUP_PAYLOAD = {
    "slug": "sample-shop",
    "username": "owner1",
    "name": "Owner",
    "email": "owner@example.com",
    "password": "secretpass",
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
def auth_session() -> Generator[Session, None, None]:
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
def auth_client(auth_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield auth_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_signup_creates_trial_tenant_and_owner(
    auth_client: TestClient,
    auth_session: Session,
):
    response = auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "owner1"
    assert body["role"] == "owner"
    assert body["is_active"] is True
    assert body["tenant_id"] is not None

    tenant = auth_session.scalar(select(Tenant).where(Tenant.slug == "sample-shop"))
    assert tenant is not None
    preset = load_personal_preset()
    assert tenant.status == "trial"
    assert tenant.edition == preset.edition.value
    assert tenant.locale == preset.locale.value
    assert tenant.roles_enabled == list(preset.roles_enabled)
    assert tenant.modules == preset.modules.model_dump()
    assert tenant.dashboard_layout == preset.dashboard_layout
    assert tenant.modules["orders"] is False
    assert tenant.modules["profit_analytics"] is False
    assert tenant.trial_ends_at is not None
    assert body["tenant_id"] == str(tenant.id)

def test_second_signup_with_new_slug_creates_another_tenant(auth_client: TestClient):
    first = auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    second = auth_client.post(
        "/api/auth/signup",
        json={
            "slug": "other-shop",
            "username": "owner1",
            "name": "Other Owner",
            "password": "secretpass",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["tenant_id"] != second.json()["tenant_id"]

def test_signup_rejects_duplicate_slug(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/signup",
        json={
            "slug": "sample-shop",
            "username": "owner2",
            "name": "Other",
            "password": "secretpass",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "slug_taken"

def test_signup_professional_copies_professional_preset(
    auth_client: TestClient,
    auth_session: Session,
):
    response = auth_client.post(
        "/api/auth/signup",
        json={
            **_SIGNUP_PAYLOAD,
            "slug": "pro-shop",
            "edition": "professional",
        },
    )

    assert response.status_code == 201
    tenant = auth_session.scalar(select(Tenant).where(Tenant.slug == "pro-shop"))
    assert tenant is not None
    preset = load_professional_preset()
    assert tenant.edition == preset.edition.value
    assert tenant.locale == preset.locale.value
    assert tenant.roles_enabled == list(preset.roles_enabled)
    assert tenant.modules == preset.modules.model_dump()
    assert tenant.dashboard_layout == preset.dashboard_layout
    assert tenant.modules["orders"] is True
    assert tenant.modules["profit_analytics"] is True
    assert tenant.modules["order_notifications"] is True
    assert "pending_orders" in tenant.dashboard_layout

def test_login_sets_cookie_with_slug(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert "token=" in (response.headers.get("set-cookie") or "")

def test_login_rejects_wrong_tenant_slug(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/login",
        json={
            "slug": "missing-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

def test_login_rejects_invalid_credentials(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

def test_login_rejects_suspended_tenant(
    auth_client: TestClient,
    auth_session: Session,
):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    tenant = auth_session.scalar(select(Tenant).where(Tenant.slug == "sample-shop"))
    assert tenant is not None
    tenant.status = "suspended"
    auth_session.commit()

    response = auth_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "tenant_suspended"

def test_login_rejects_expired_trial(
    auth_client: TestClient,
    auth_session: Session,
):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    tenant = auth_session.scalar(select(Tenant).where(Tenant.slug == "sample-shop"))
    assert tenant is not None
    tenant.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    auth_session.commit()

    response = auth_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "trial_expired"

def test_logout_clears_cookie(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    auth_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    response = auth_client.post("/api/auth/logout")

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie") or ""
    assert "token=" in set_cookie
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()
