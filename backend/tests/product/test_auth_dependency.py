from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.security import create_token
from dependencies.product.auth import get_current_user
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
def auth_probe_client(auth_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")

    @app.get("/api/auth/probe")
    def probe(current_user: dict = Depends(get_current_user)):
        return current_user

    def override_get_db() -> Generator[Session, None, None]:
        yield auth_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_get_current_user_returns_owner_after_login(auth_probe_client: TestClient):
    auth_probe_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    auth_probe_client.post(
        "/api/auth/login",
        json={"username": "owner1", "password": "secretpass"},
    )

    response = auth_probe_client.get("/api/auth/probe")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "owner1"
    assert body["role"] == "owner"
    assert body["is_active"] is True

def test_get_current_user_without_cookie_returns_401(auth_probe_client: TestClient):
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_current_user_rejects_invalid_token(auth_probe_client: TestClient):
    auth_probe_client.cookies.set("token", "not-a-valid-jwt")
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"

def test_get_current_user_rejects_non_uuid_sub(auth_probe_client: TestClient):
    token = create_token({"sub": "507f1f77bcf86cd799439011", "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"

def test_get_current_user_returns_404_when_user_missing(auth_probe_client: TestClient):
    token = create_token({"sub": str(uuid4()), "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_current_user_rejects_inactive_owner(auth_session: Session, auth_probe_client: TestClient):
    owner = User(
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

    token = create_token({"sub": str(owner.id), "role": "owner"})
    auth_probe_client.cookies.set("token", token)
    response = auth_probe_client.get("/api/auth/probe")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
