from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from models.product.user import User
from routes.product.auth import router as product_auth_router

_SIGNUP_PAYLOAD = {
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

    monkeypatch.setattr("routes.product.auth.hash_password", fake_hash)
    monkeypatch.setattr("routes.product.auth.verify_password", fake_verify)

@pytest.fixture
def auth_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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

def test_signup_creates_owner(auth_client: TestClient):
    response = auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "owner1"
    assert body["role"] == "owner"
    assert body["is_active"] is True
    assert "id" in body

def test_second_signup_returns_403(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/signup",
        json={
            "username": "owner2",
            "name": "Other",
            "password": "secretpass",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Signup is disabled after the owner account is created"

def test_login_sets_cookie(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "owner1", "password": "secretpass"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert "token=" in (response.headers.get("set-cookie") or "")

def test_login_rejects_invalid_credentials(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "owner1", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_logout_clears_cookie(auth_client: TestClient):
    auth_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    auth_client.post(
        "/api/auth/login",
        json={"username": "owner1", "password": "secretpass"},
    )

    response = auth_client.post("/api/auth/logout")

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie") or ""
    assert "token=" in set_cookie
    assert "Max-Age=0" in set_cookie or 'max-age=0' in set_cookie.lower()
