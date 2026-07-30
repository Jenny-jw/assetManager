from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from core.deployment import Edition
from models.stock import Stock
from schemas.stock import validate_weight_grams_for_edition

_SORT_COLUMNS = {
    "created_at": Stock.created_at,
    "name": Stock.name,
    "genre": Stock.genre,
    "origin": Stock.origin,
    "quantity": Stock.quantity,
    "score": Stock.score,
    "price_per_jin": Stock.price_per_jin,
    "harvest_time": Stock.harvest_time,
}

def active_stocks_select(*, tenant_id: UUID) -> Select[tuple[Stock]]:
    return select(Stock).where(
        Stock.deleted_at.is_(None),
        Stock.tenant_id == tenant_id,
    )

def _apply_stock_list_filters(
    statement: Select[tuple[Stock]],
    *,
    search: str | None,
    genre: str | None,
    origin: str | None,
) -> Select[tuple[Stock]]:
    if genre is not None:
        statement = statement.where(Stock.genre == genre)
    if origin is not None:
        statement = statement.where(Stock.origin == origin)
    if search:
        statement = statement.where(Stock.name.ilike(f"%{search}%"))
    return statement

def filtered_active_stocks_select(
    *,
    tenant_id: UUID,
    search: str | None = None,
    genre: str | None = None,
    origin: str | None = None,
) -> Select[tuple[Stock]]:
    return _apply_stock_list_filters(
        active_stocks_select(tenant_id=tenant_id),
        search=search,
        genre=genre,
        origin=origin,
    )

def count_active_stocks(db: Session, *, tenant_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Stock)
            .where(
                Stock.deleted_at.is_(None),
                Stock.tenant_id == tenant_id,
            )
        )
        or 0
    )

def list_active_stocks(
    db: Session,
    *,
    tenant_id: UUID,
    page: int,
    limit: int,
    sort_by: str,
    sort_direction: str,
    search: str | None = None,
    genre: str | None = None,
    origin: str | None = None,
) -> tuple[list[Stock], int]:
    statement = filtered_active_stocks_select(
        tenant_id=tenant_id,
        search=search,
        genre=genre,
        origin=origin,
    )
    total = int(db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    column = _SORT_COLUMNS[sort_by]
    order = column.asc() if sort_direction == "asc" else column.desc()
    statement = statement.order_by(order)
    offset = (page - 1) * limit
    rows = list(db.scalars(statement.offset(offset).limit(limit)).all())
    return rows, total

def get_active_stock(db: Session, stock_id: UUID, *, tenant_id: UUID) -> Stock | None:
    return db.scalar(
        active_stocks_select(tenant_id=tenant_id).where(Stock.id == stock_id)
    )

def coerce_weight_grams_for_edition(
    weight_grams: int | None,
    edition: Edition,
) -> int | None:
    return validate_weight_grams_for_edition(weight_grams, edition)
