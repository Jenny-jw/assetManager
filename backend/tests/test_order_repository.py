from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models.order import (
    Order,
    OrderItem,
    OrderStatus,
    StockMovement,
    StockMovementReason,
)
from repositories.postgres.order_repository import OrderRepository

_TENANT_A = uuid4()
_TENANT_B = uuid4()
_USER_A = uuid4()
_STOCK_A = uuid4()

@pytest.fixture
def order_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    try:
        yield session
    finally:
        session.close()
        StockMovement.__table__.drop(bind=engine)
        OrderItem.__table__.drop(bind=engine)
        Order.__table__.drop(bind=engine)
        engine.dispose()

def _repo(session: Session, tenant_id=_TENANT_A) -> OrderRepository:
    return OrderRepository(session, tenant_id=tenant_id)

def _create_order(session: Session, *, tenant_id=_TENANT_A, stock_name: str = "Alishan") -> Order:
    return _repo(session, tenant_id).create(
        created_by=_USER_A,
        status=OrderStatus.pending,
        total_amount=150,
        items=[
            {
                "stock_id": _STOCK_A,
                "stock_name": stock_name,
                "quantity": 1,
                "unit_price": 150,
                "line_total": 150,
            }
        ],
    )

def test_create_persists_order_and_items_for_tenant(order_session: Session):
    order = _create_order(order_session)

    loaded = _repo(order_session).get(order.id)
    assert loaded is not None
    assert loaded.tenant_id == _TENANT_A
    assert loaded.status == OrderStatus.pending.value
    assert loaded.total_amount == 150
    assert len(loaded.items) == 1
    assert loaded.items[0].stock_name == "Alishan"

def test_get_returns_none_for_other_tenant(order_session: Session):
    order = _create_order(order_session)

    assert _repo(order_session, _TENANT_B).get(order.id) is None

def test_list_excludes_other_tenant_orders(order_session: Session):
    _create_order(order_session, stock_name="TenantA")
    _create_order(order_session, tenant_id=_TENANT_B, stock_name="TenantB")

    rows, total = _repo(order_session).list(page=1, limit=20)

    assert total == 1
    assert len(rows) == 1
    assert rows[0].items[0].stock_name == "TenantA"

def test_list_can_filter_by_status(order_session: Session):
    _create_order(order_session)
    _repo(order_session).create(
        created_by=_USER_A,
        status=OrderStatus.cancelled,
        total_amount=0,
        items=[
            {
                "stock_id": _STOCK_A,
                "stock_name": "Cancelled",
                "quantity": 1,
                "unit_price": 0,
                "line_total": 0,
            }
        ],
    )

    rows, total = _repo(order_session).list(page=1, limit=20, status=OrderStatus.pending)

    assert total == 1
    assert rows[0].status == OrderStatus.pending.value

def test_add_movement_is_tenant_scoped(order_session: Session):
    order = _create_order(order_session)
    movement = _repo(order_session).add_movement(
        stock_id=_STOCK_A,
        delta=-1,
        quantity_before=2,
        quantity_after=1,
        reason=StockMovementReason.order.value,
        ref_type="order",
        ref_id=order.id,
        created_by=_USER_A,
    )

    assert movement.tenant_id == _TENANT_A
    assert _repo(order_session).list_movements_for_ref(ref_type="order", ref_id=order.id)
    assert (
        _repo(order_session, _TENANT_B).list_movements_for_ref(
            ref_type="order",
            ref_id=order.id,
        )
        == []
    )

def test_claim_pending_moves_status_once_for_tenant(order_session: Session):
    order = _create_order(order_session)
    repo = _repo(order_session)

    claimed = repo.claim_pending(order.id, new_status=OrderStatus.confirmed)
    repo.commit()

    assert claimed is not None
    assert claimed.status == OrderStatus.confirmed.value
    assert repo.claim_pending(order.id, new_status=OrderStatus.cancelled) is None
    assert (
        _repo(order_session, _TENANT_B).claim_pending(
            order.id,
            new_status=OrderStatus.cancelled,
        )
        is None
    )