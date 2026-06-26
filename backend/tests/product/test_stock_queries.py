from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.deployment import Edition
from models.stock import Stock
from services.product.stock_queries import (
    active_stocks_select,
    coerce_weight_grams_for_edition,
    get_active_stock,
)

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

def _insert_stock(session: Session, *, name: str, deleted: bool = False) -> Stock:
    stock = Stock(
        id=uuid4(),
        name=name,
        genre="Oolong",
        quantity=1,
        deleted_at=datetime.now(timezone.utc) if deleted else None,
    )
    session.add(stock)
    session.commit()
    session.refresh(stock)
    return stock

def test_get_active_stock_returns_row_when_not_deleted(stock_session: Session):
    stock = _insert_stock(stock_session, name="Active")

    found = get_active_stock(stock_session, stock.id)

    assert found is not None
    assert found.id == stock.id
    assert found.name == "Active"

def test_get_active_stock_returns_none_when_soft_deleted(stock_session: Session):
    stock = _insert_stock(stock_session, name="Deleted", deleted=True)

    assert get_active_stock(stock_session, stock.id) is None

def test_active_stocks_select_excludes_soft_deleted(stock_session: Session):
    _insert_stock(stock_session, name="Keep")
    _insert_stock(stock_session, name="Gone", deleted=True)

    rows = list(stock_session.scalars(active_stocks_select()).all())

    assert len(rows) == 1
    assert rows[0].name == "Keep"

def test_coerce_weight_grams_personal_allows_75_and_150():
    assert coerce_weight_grams_for_edition(75, Edition.personal) == 75
    assert coerce_weight_grams_for_edition(150, Edition.personal) == 150

def test_coerce_weight_grams_personal_rejects_other_values():
    with pytest.raises(ValueError, match="75 or 150"):
        coerce_weight_grams_for_edition(100, Edition.personal)

def test_coerce_weight_grams_professional_allows_positive():
    assert coerce_weight_grams_for_edition(100, Edition.professional) == 100

def test_coerce_weight_grams_none_passes_through():
    assert coerce_weight_grams_for_edition(None, Edition.personal) is None
