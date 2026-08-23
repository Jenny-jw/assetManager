from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from core.db import get_db
from core.security import create_token
from core.tenant import get_request_tenant_id
from dependencies.auth import get_current_user
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

def _make_tenant(**overrides) -> Tenant:
    values = {
        "slug": "sample-shop",
        "edition": "personal",
        "locale": "zh-TW",
        "roles_enabled": ["owner"],
        "modules": {"inventory": True, "orders": False},
        "dashboard_layout": ["summary"],
        "status": "trial",
        "trial_ends_at": datetime.now(timezone.utc) + timedelta(days=90),
    }
    values.update(overrides)
    return Tenant(**values)

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
def auth_probe_client(auth_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")

    @app.get("/api/auth/probe")
    def probe(request: Request, current_user: dict = Depends(get_current_user)):
        resolved = get_request_tenant_id(request)
        return {
            **current_user,
            "resolved_tenant_id": str(resolved) if resolved is not None else None,
        }

    def override_get_db() -> Generator[Session, None, None]:
        yield auth_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_get_current_user_returns_owner_after_login(auth_probe_client: TestClient):
    signup = auth_probe_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    assert signup.status_code == 201
    tenant_id = signup.json()["tenant_id"]

    auth_probe_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )

    response = auth_probe_client.get("/api/auth/probe")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "owner1"
    assert body["role"] == "owner"
    assert body["is_active"] is True
    assert body["tenant_id"] == tenant_id
    assert body["resolved_tenant_id"] == tenant_id

def test_get_current_user_without_cookie_returns_401(auth_probe_client: TestClient):
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "not_authenticated"

def test_get_current_user_rejects_invalid_token(auth_probe_client: TestClient):
    auth_probe_client.cookies.set("token", "not-a-valid-jwt")
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_token"

def test_get_current_user_rejects_non_uuid_sub(auth_probe_client: TestClient):
    token = create_token({"sub": "507f1f77bcf86cd799439011", "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_token_payload"

def test_get_current_user_returns_404_when_user_missing(auth_probe_client: TestClient):
    token = create_token(
        {
            "sub": str(uuid4()),
            "role": "owner",
            "tenant_id": str(uuid4()),
        }
    )
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"

def test_get_current_user_rejects_inactive_owner(auth_session: Session, auth_probe_client: TestClient):
    tenant = _make_tenant()
    auth_session.add(tenant)
    auth_session.flush()
    owner = User(
        tenant_id=tenant.id,
        username="owner1",
        name="Owner",
        email="owner@example.com",
        hashed_password="hashed:secretpass",
        role="owner",
        is_active=False,
    )
    auth_session.add(owner)
    auth_session.commit()
    auth_session.refresh(owner)

    token = create_token(
        {
            "sub": str(owner.id),
            "role": "owner",
            "tenant_id": str(tenant.id),
        }
    )
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "not_authenticated"

def test_login_includes_tenant_id_claim_for_tenant_bound_owner(
    auth_probe_client: TestClient,
):
    signup = auth_probe_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    assert signup.status_code == 201
    tenant_id = signup.json()["tenant_id"]

    login = auth_probe_client.post(
        "/api/auth/login",
        json={
            "slug": "sample-shop",
            "username": "owner1",
            "password": "secretpass",
        },
    )
    assert login.status_code == 200

    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["resolved_tenant_id"] == tenant_id
    assert body["username"] == "owner1"

def test_get_current_user_scopes_by_jwt_tenant_id(
    auth_session: Session,
    auth_probe_client: TestClient,
):
    tenant = _make_tenant(slug="tenant-a")
    other = _make_tenant(slug="tenant-b")
    auth_session.add_all([tenant, other])
    auth_session.flush()
    owner = User(
        tenant_id=tenant.id,
        username="owner1",
        name="Owner",
        email="owner@example.com",
        hashed_password="hashed:secretpass",
        role="owner",
        is_active=True,
    )
    auth_session.add(owner)
    auth_session.commit()
    auth_session.refresh(owner)

    mismatched = create_token(
        {
            "sub": str(owner.id),
            "role": "owner",
            "tenant_id": str(other.id),
        }
    )
    auth_probe_client.cookies.set("token", mismatched)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"

def test_get_current_user_requires_tenant_claim(auth_probe_client: TestClient):
    token = create_token({"sub": str(uuid4()), "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_token_payload"

def test_get_current_user_rejects_tenant_bound_user_without_tenant_claim(
    auth_session: Session,
    auth_probe_client: TestClient,
):
    tenant = _make_tenant()
    auth_session.add(tenant)
    auth_session.flush()
    owner = User(
        tenant_id=tenant.id,
        username="owner1",
        name="Owner",
        email="owner@example.com",
        hashed_password="hashed:secretpass",
        role="owner",
        is_active=True,
    )
    auth_session.add(owner)
    auth_session.commit()
    auth_session.refresh(owner)

    token = create_token({"sub": str(owner.id), "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_token_payload"

def test_get_current_user_rejects_non_uuid_tenant_claim(
    auth_session: Session,
    auth_probe_client: TestClient,
):
    tenant = _make_tenant()
    auth_session.add(tenant)
    auth_session.flush()
    owner = User(
        tenant_id=tenant.id,
        username="owner1",
        name="Owner",
        email="owner@example.com",
        hashed_password="hashed:secretpass",
        role="owner",
        is_active=True,
    )
    auth_session.add(owner)
    auth_session.commit()
    auth_session.refresh(owner)

    token = create_token(
        {
            "sub": str(owner.id),
            "role": "owner",
            "tenant_id": "not-a-uuid",
        }
    )
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_token_payload"
