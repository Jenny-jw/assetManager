from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.deployment import DeploymentConfig, get_deployment, load_professional_preset
from core.errors import register_exception_handlers
from core.tea_pricing import line_unrealized_profit
from dependencies.auth import get_current_user
from models.stock import Stock
from models.tenant import Tenant
from models.user import User
from modules.analytics import router as analytics_router
from repositories.postgres.stock_repository import StockRepository
from services.profit_analytics_service import build_profit_summary

_TENANT_ID = "a1111111-b222-c333-d444-e55555555555"
_OWNER_ID = "a0000000-b000-c000-d000-e00000000001"

_OWNER: dict[str, Any] = {
    "id": _OWNER_ID,
    "tenant_id": _TENANT_ID,
    "username": "owner1",
    "role": "owner",
    "name": "Owner",
    "email": "owner@example.com",
    "is_active": True,
}

@pytest.fixture
def profit_session() -> Generator[Session, None, None]:
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
    session = session_factory()
    session.add(
        Tenant(
            id=UUID(_TENANT_ID),
            slug="pro-profit",
            edition="professional",
            locale="zh-TW",
            roles_enabled=["owner"],
            modules={"inventory": True, "orders": True, "profit_analytics": True},
            dashboard_layout=["summary", "profit"],
            status="active",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Stock.__table__.drop(bind=engine)
        User.__table__.drop(bind=engine)
        Tenant.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def professional_deployment() -> DeploymentConfig:
    return load_professional_preset()

@pytest.fixture
def profit_client(
    profit_session: Session,
    professional_deployment: DeploymentConfig,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(analytics_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield profit_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _OWNER
    app.dependency_overrides[get_deployment] = lambda: professional_deployment
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def _insert_stock(session: Session, **fields: object) -> Stock:
    payload = {
        "name": "Alishan Oolong",
        "genre": "Oolong",
        "origin": "Alishan",
        "weight_grams": 75,
        "quantity": 2,
        "price_per_jin": 1200,
        "cost_per_jin": 800,
        **fields,
    }
    return StockRepository(session, tenant_id=UUID(_TENANT_ID)).create(**payload)

def test_line_unrealized_profit_requires_price_and_cost():
    assert line_unrealized_profit(1200, 800, 75, 2) == 100
    assert line_unrealized_profit(1200, None, 75, 2) is None
    assert line_unrealized_profit(None, 800, 75, 2) is None

def test_build_profit_summary_counts_complete_and_uncosted_lines(
    profit_session: Session,
):
    _insert_stock(profit_session)
    _insert_stock(
        profit_session,
        name="No Cost",
        cost_per_jin=None,
        quantity=1,
    )

    summary = build_profit_summary(
        StockRepository(profit_session, tenant_id=UUID(_TENANT_ID))
    )

    assert summary.priced_assets == 2
    assert summary.costed_assets == 1
    assert summary.complete_assets == 1
    assert summary.uncosted_assets == 1
    assert summary.total_retail_value == 300 + 150
    assert summary.total_cost_value == 200
    assert summary.unrealized_profit == 100
    assert summary.by_genre == {"Oolong": 100}
    assert summary.by_origin == {"Alishan": 100}

def test_profit_endpoint_returns_summary(
    profit_client: TestClient,
    profit_session: Session,
):
    _insert_stock(profit_session)

    response = profit_client.get("/api/analytics/profit")

    assert response.status_code == 200
    body = response.json()
    assert body["total_retail_value"] == 300
    assert body["total_cost_value"] == 200
    assert body["unrealized_profit"] == 100
    assert body["complete_assets"] == 1
    assert body["lines"][0]["name"] == "Alishan Oolong"
    assert body["lines"][0]["profit"] == 100

def test_personal_deployment_rejects_profit_endpoint(
    profit_session: Session,
):
    from core.deployment import load_personal_preset

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(analytics_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield profit_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _OWNER
    app.dependency_overrides[get_deployment] = load_personal_preset
    with TestClient(app) as client:
        response = client.get("/api/analytics/profit")

    assert response.status_code == 403
    assert response.json()["detail"] == "module_disabled"