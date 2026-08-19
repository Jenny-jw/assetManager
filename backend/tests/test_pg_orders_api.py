from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.deployment import DeploymentConfig, get_deployment, load_professional_preset
from core.errors import register_exception_handlers
from dependencies.auth import get_current_user
from models.order import Order, OrderItem, StockMovement
from models.stock import Stock
from models.tenant import Tenant
from models.user import User
from modules.orders import router as orders_router
from repositories.postgres.stock_repository import StockRepository

_TENANT_A = "a1111111-b222-c333-d444-e55555555555"
_TENANT_B = "b1111111-c222-d333-e444-f55555555555"
_OWNER_A_ID = "a0000000-b000-c000-d000-e00000000001"
_OWNER_B_ID = "a0000000-b000-c000-d000-e00000000002"

_OWNER_A: dict[str, Any] = {
    "id": _OWNER_A_ID,
    "tenant_id": _TENANT_A,
    "username": "owner-a",
    "role": "owner",
    "name": "Owner A",
    "email": "a@example.com",
    "is_active": True,
}

_OWNER_B: dict[str, Any] = {
    "id": _OWNER_B_ID,
    "tenant_id": _TENANT_B,
    "username": "owner-b",
    "role": "owner",
    "name": "Owner B",
    "email": "b@example.com",
    "is_active": True,
}

_STOCK_FIELDS = {
    "name": "Alishan Oolong",
    "genre": "Oolong",
    "origin": "Alishan",
    "weight_grams": 75,
    "quantity": 4,
    "price_per_jin": 1200,
}

@pytest.fixture
def order_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    Stock.__table__.create(bind=engine)
    Order.__table__.create(bind=engine)
    OrderItem.__table__.create(bind=engine)
    StockMovement.__table__.create(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = session_factory()
    session.add_all(
        [
            Tenant(
                id=UUID(_TENANT_A),
                slug="pro-shop-a",
                edition="professional",
                locale="zh-TW",
                roles_enabled=["owner"],
                modules={"inventory": True, "orders": True},
                dashboard_layout=["summary", "pending_orders"],
                status="active",
            ),
            Tenant(
                id=UUID(_TENANT_B),
                slug="pro-shop-b",
                edition="professional",
                locale="zh-TW",
                roles_enabled=["owner"],
                modules={"inventory": True, "orders": True},
                dashboard_layout=["summary", "pending_orders"],
                status="active",
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        StockMovement.__table__.drop(bind=engine)
        OrderItem.__table__.drop(bind=engine)
        Order.__table__.drop(bind=engine)
        Stock.__table__.drop(bind=engine)
        User.__table__.drop(bind=engine)
        Tenant.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def professional_deployment() -> DeploymentConfig:
    return load_professional_preset()

@pytest.fixture
def order_client(
    order_session: Session,
    professional_deployment: DeploymentConfig,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(orders_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield order_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _OWNER_A
    app.dependency_overrides[get_deployment] = lambda: professional_deployment
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def _insert_stock(
    session: Session,
    *,
    tenant_id: str = _TENANT_A,
    **overrides: object,
) -> Stock:
    fields = {**_STOCK_FIELDS, **overrides}
    return StockRepository(session, tenant_id=UUID(tenant_id)).create(**fields)

def test_create_order_is_pending_and_does_not_change_stock(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)

    response = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 2}]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["user_id"] == _OWNER_A_ID
    assert body["total_amount"] == 300
    assert body["items"][0]["stock_id"] == str(stock.id)
    assert body["items"][0]["stock_name"] == "Alishan Oolong"
    assert body["items"][0]["unit_price"] == 150
    assert body["items"][0]["line_total"] == 300
    assert body["items"][0]["stock_available"] is True

    order_session.refresh(stock)
    assert stock.quantity == 4
    assert order_session.scalar(select(StockMovement)) is None

def test_list_and_get_order_include_items(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 1}]},
    )
    order_id = created.json()["id"]

    listed = order_client.get("/api/orders/")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["data"][0]["id"] == order_id

    pending = order_client.get("/api/orders/", params={"status": "pending"})
    assert pending.json()["total"] == 1

    confirmed = order_client.get("/api/orders/", params={"status": "confirmed"})
    assert confirmed.json()["total"] == 0

    fetched = order_client.get(f"/api/orders/{order_id}")
    assert fetched.status_code == 200
    assert fetched.json()["items"][0]["quantity"] == 1

def test_create_rejects_invalid_and_missing_stock(order_client: TestClient):
    invalid = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": "not-a-uuid", "quantity": 1}]},
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "invalid_stock_id"

    missing = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(uuid4()), "quantity": 1}]},
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "stock_not_found"

def test_create_rejects_stock_without_price_or_weight(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session, price_per_jin=None)

    response = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 1}]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "stock_not_orderable"

def test_get_rejects_invalid_and_unknown_order_id(order_client: TestClient):
    invalid = order_client.get("/api/orders/not-a-uuid")
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "invalid_order_id"

    missing = order_client.get(f"/api/orders/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "order_not_found"

def test_tenant_cannot_read_or_order_other_tenant_stock(
    order_client: TestClient,
    order_session: Session,
):
    stock_a = _insert_stock(order_session, tenant_id=_TENANT_A)
    stock_b = _insert_stock(order_session, tenant_id=_TENANT_B, name="Other Shop Tea")
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock_a.id), "quantity": 1}]},
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    cross_stock = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock_b.id), "quantity": 1}]},
    )
    assert cross_stock.status_code == 404
    assert cross_stock.json()["detail"] == "stock_not_found"

    order_client.app.dependency_overrides[get_current_user] = lambda: _OWNER_B
    listed = order_client.get("/api/orders/")
    assert listed.status_code == 200
    assert listed.json()["total"] == 0

    fetched = order_client.get(f"/api/orders/{order_id}")
    assert fetched.status_code == 404
    assert fetched.json()["detail"] == "order_not_found"

def test_unauthenticated_orders_return_not_authenticated(
    order_session: Session,
    professional_deployment: DeploymentConfig,
):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(orders_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield order_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_deployment] = lambda: professional_deployment
    with TestClient(app) as client:
        response = client.get("/api/orders/")

    assert response.status_code == 401
    assert response.json()["detail"] == "not_authenticated"

def test_approve_confirms_order_and_decrements_stock(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 2}]},
    )
    order_id = created.json()["id"]

    response = order_client.patch(f"/api/orders/{order_id}/approve")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    order_session.refresh(stock)
    assert stock.quantity == 2
    movements = list(order_session.scalars(select(StockMovement)).all())
    assert len(movements) == 1
    assert movements[0].delta == -2
    assert movements[0].quantity_before == 4
    assert movements[0].quantity_after == 2
    assert movements[0].reason == "order"
    assert movements[0].ref_type == "order"
    assert str(movements[0].ref_id) == order_id

def test_reject_cancels_without_changing_stock(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 2}]},
    )
    order_id = created.json()["id"]

    response = order_client.patch(f"/api/orders/{order_id}/reject")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    order_session.refresh(stock)
    assert stock.quantity == 4
    assert order_session.scalar(select(StockMovement)) is None

def test_second_approve_returns_conflict_and_does_not_deduct_again(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 2}]},
    )
    order_id = created.json()["id"]

    first = order_client.patch(f"/api/orders/{order_id}/approve")
    second = order_client.patch(f"/api/orders/{order_id}/approve")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == "order_not_pending"
    order_session.refresh(stock)
    assert stock.quantity == 2
    assert len(list(order_session.scalars(select(StockMovement)).all())) == 1

def test_approve_insufficient_stock_leaves_order_pending(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 2}]},
    )
    order_id = created.json()["id"]
    StockRepository(order_session, tenant_id=UUID(_TENANT_A)).update(
        stock, {"quantity": 1}
    )

    response = order_client.patch(f"/api/orders/{order_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "insufficient_stock"
    fetched = order_client.get(f"/api/orders/{order_id}")
    assert fetched.json()["status"] == "pending"
    order_session.refresh(stock)
    assert stock.quantity == 1
    assert order_session.scalar(select(StockMovement)) is None

def test_approve_soft_deleted_stock_does_not_partially_deduct(
    order_client: TestClient,
    order_session: Session,
):
    keep = _insert_stock(order_session, name="Keep Tea", quantity=5)
    gone = _insert_stock(order_session, name="Gone Tea", quantity=5)
    created = order_client.post(
        "/api/orders/",
        json={
            "items": [
                {"stock_id": str(keep.id), "quantity": 1},
                {"stock_id": str(gone.id), "quantity": 1},
            ]
        },
    )
    order_id = created.json()["id"]
    StockRepository(order_session, tenant_id=UUID(_TENANT_A)).soft_delete(gone)

    response = order_client.patch(f"/api/orders/{order_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "stock_not_found"
    fetched = order_client.get(f"/api/orders/{order_id}")
    assert fetched.json()["status"] == "pending"
    order_session.refresh(keep)
    assert keep.quantity == 5
    assert order_session.scalar(select(StockMovement)) is None

def test_approve_rejects_when_combined_lines_exceed_stock(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={
            "items": [
                {"stock_id": str(stock.id), "quantity": 2},
                {"stock_id": str(stock.id), "quantity": 3},
            ]
        },
    )
    order_id = created.json()["id"]

    response = order_client.patch(f"/api/orders/{order_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "insufficient_stock"
    fetched = order_client.get(f"/api/orders/{order_id}")
    assert fetched.json()["status"] == "pending"
    order_session.refresh(stock)
    assert stock.quantity == 4

def test_tenant_cannot_approve_or_reject_other_tenant_order(
    order_client: TestClient,
    order_session: Session,
):
    stock = _insert_stock(order_session)
    created = order_client.post(
        "/api/orders/",
        json={"items": [{"stock_id": str(stock.id), "quantity": 1}]},
    )
    order_id = created.json()["id"]
    order_client.app.dependency_overrides[get_current_user] = lambda: _OWNER_B

    approved = order_client.patch(f"/api/orders/{order_id}/approve")
    rejected = order_client.patch(f"/api/orders/{order_id}/reject")

    assert approved.status_code == 404
    assert approved.json()["detail"] == "order_not_found"
    assert rejected.status_code == 404
    assert rejected.json()["detail"] == "order_not_found"

def test_approve_rejects_invalid_and_unknown_order_id(order_client: TestClient):
    invalid = order_client.patch("/api/orders/not-a-uuid/approve")
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "invalid_order_id"

    missing = order_client.patch(f"/api/orders/{uuid4()}/approve")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "order_not_found"