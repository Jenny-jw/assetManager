from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models.stock import Stock
from repositories.postgres.stock_repository import StockRepository

_TENANT_A = uuid4()
_TENANT_B = uuid4()

@pytest.fixture
def stock_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
        Stock.__table__.drop(bind=engine)
        engine.dispose()

def _repo(session: Session, tenant_id=_TENANT_A) -> StockRepository:
    return StockRepository(session, tenant_id=tenant_id)

def _insert_stock(
    session: Session,
    *,
    name: str,
    tenant_id=_TENANT_A,
    deleted: bool = False,
) -> Stock:
    stock = Stock(
        id=uuid4(),
        tenant_id=tenant_id,
        name=name,
        genre="Oolong",
        quantity=1,
        deleted_at=datetime.now(timezone.utc) if deleted else None,
    )
    session.add(stock)
    session.commit()
    session.refresh(stock)
    return stock

def test_get_active_returns_row_when_not_deleted(stock_session: Session):
    stock = _insert_stock(stock_session, name="Active")

    found = _repo(stock_session).get_active(stock.id)

    assert found is not None
    assert found.id == stock.id
    assert found.name == "Active"

def test_get_active_returns_none_when_soft_deleted(stock_session: Session):
    stock = _insert_stock(stock_session, name="Deleted", deleted=True)

    assert _repo(stock_session).get_active(stock.id) is None

def test_get_active_returns_none_for_other_tenant(stock_session: Session):
    stock = _insert_stock(stock_session, name="OtherTenant", tenant_id=_TENANT_B)

    assert _repo(stock_session).get_active(stock.id) is None

def test_list_all_active_excludes_soft_deleted(stock_session: Session):
    _insert_stock(stock_session, name="Keep")
    _insert_stock(stock_session, name="Gone", deleted=True)

    rows = _repo(stock_session).list_all_active()

    assert len(rows) == 1
    assert rows[0].name == "Keep"

def test_list_all_active_scopes_to_tenant(stock_session: Session):
    _insert_stock(stock_session, name="A", tenant_id=_TENANT_A)
    _insert_stock(stock_session, name="B", tenant_id=_TENANT_B)

    rows = _repo(stock_session).list_all_active()

    assert len(rows) == 1
    assert rows[0].name == "A"

def test_create_assigns_repository_tenant(stock_session: Session):
    stock = _repo(stock_session).create(name="New Tea", genre="Oolong", quantity=2)

    assert stock.tenant_id == _TENANT_A
    assert stock.name == "New Tea"
    assert _repo(stock_session).get_active(stock.id) is not None

def test_update_and_soft_delete(stock_session: Session):
    stock = _insert_stock(stock_session, name="Before")
    repo = _repo(stock_session)

    updated = repo.update(stock, {"name": "After", "quantity": 5})
    assert updated.name == "After"
    assert updated.quantity == 5
    assert updated.updated_at is not None

    repo.soft_delete(updated)
    assert repo.get_active(updated.id) is None

def test_list_active_paginates_and_filters(stock_session: Session):
    _insert_stock(stock_session, name="Alishan Oolong")
    _insert_stock(stock_session, name="Sencha")
    _insert_stock(stock_session, name="Other", tenant_id=_TENANT_B)

    repo = _repo(stock_session)
    rows, total = repo.list_active(
        page=1,
        limit=10,
        sort_by="name",
        sort_direction="asc",
        search="oolong",
    )

    assert total == 1
    assert len(rows) == 1
    assert rows[0].name == "Alishan Oolong"