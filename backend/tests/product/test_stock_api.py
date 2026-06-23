from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.deployment import DeploymentConfig, get_deployment, load_personal_preset
from dependencies.product.auth import get_current_user
from models.product.stock import Stock
from models.product.user import User
from routes.product.stock import router as product_stock_router

_OWNER: dict[str, Any] = {
    "id": "00000000-0000-0000-0000-000000000001",
    "username": "owner1",
    "role": "owner",
    "name": "Owner",
    "email": "owner@example.com",
    "is_active": True,
}

_STOCK_PAYLOAD = {
    "name": "Alishan Oolong",
    "genre": "Oolong",
    "origin": "Alishan",
    "weight_grams": 75,
    "quantity": 2,
    "price_per_jin": 1200,
}

@pytest.fixture
def stock_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=engine)
    Stock.__table__.create(bind=engine)
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
        Stock.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def personal_deployment() -> DeploymentConfig:
    return load_personal_preset()

@pytest.fixture
def stock_client(
    stock_session: Session,
    personal_deployment: DeploymentConfig,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_stock_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield stock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _OWNER
    app.dependency_overrides[get_deployment] = lambda: personal_deployment
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_create_stock_returns_201(stock_client: TestClient):
    response = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alishan Oolong"
    assert body["weight_grams"] == 75
    assert body["quantity"] == 2
    assert "id" in body
    assert "created_at" in body

def test_create_stock_rejects_invalid_weight_for_personal(stock_client: TestClient):
    response = stock_client.post(
        "/api/stock/",
        json={**_STOCK_PAYLOAD, "weight_grams": 100},
    )

    assert response.status_code == 400
    assert "75 or 150" in response.json()["detail"]

def test_create_stock_requires_owner(stock_session: Session, personal_deployment: DeploymentConfig):
    app = FastAPI()
    app.include_router(product_stock_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield stock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_deployment] = lambda: personal_deployment

    with TestClient(app) as client:
        response = client.post("/api/stock/", json=_STOCK_PAYLOAD)

    assert response.status_code == 401
