from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from models.user import User
from routes.auth import router as product_auth_router
from routes.security import router as product_security_router

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

    monkeypatch.setattr("routes.auth.hash_password", fake_hash)
    monkeypatch.setattr("routes.auth.verify_password", fake_verify)

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
def auth_me_client(auth_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")
    app.include_router(product_security_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield auth_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_me_returns_owner_profile_after_login(auth_me_client: TestClient):
    auth_me_client.post("/api/auth/signup", json=_SIGNUP_PAYLOAD)
    auth_me_client.post(
        "/api/auth/login",
        json={"username": "owner1", "password": "secretpass"},
    )

    response = auth_me_client.get("/api/security/me")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "owner1"
    assert body["name"] == "Owner"
    assert body["email"] == "owner@example.com"
    assert body["role"] == "owner"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body

def test_me_without_cookie_returns_401(auth_me_client: TestClient):
    response = auth_me_client.get("/api/security/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
