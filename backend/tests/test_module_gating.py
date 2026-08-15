from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from models.tenant import Tenant
from models.user import User
from modules.inventory import router as stock_router
from modules.orders import router as orders_router
from routes.auth import router as product_auth_router

_PERSONAL_SIGNUP = {
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
def module_session(monkeypatch) -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    from models.stock import Stock

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
def module_client(module_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_auth_router, prefix="/api")
    app.include_router(stock_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield module_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def _signup_and_login(client: TestClient, *, edition: str = "personal", slug: str = "sample-shop"):
    signup = client.post(
        "/api/auth/signup",
        json={**_PERSONAL_SIGNUP, "slug": slug, "edition": edition},
    )
    assert signup.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"slug": slug, "username": "owner1", "password": "secretpass"},
    )
    assert login.status_code == 200

def test_personal_tenant_orders_return_module_disabled(module_client: TestClient):
    _signup_and_login(module_client, edition="personal", slug="sample-shop")

    response = module_client.get("/api/orders/")

    assert response.status_code == 403
    assert response.json()["detail"] == "module_disabled"

def test_personal_tenant_stock_remains_available(module_client: TestClient, module_session: Session):
    _signup_and_login(module_client, edition="personal", slug="tea-shop")

    # Stock module enabled; auth passes. Empty list is enough to prove module gate passed.
    response = module_client.get("/api/stock/")

    assert response.status_code == 200
    assert response.json()["data"] == []
