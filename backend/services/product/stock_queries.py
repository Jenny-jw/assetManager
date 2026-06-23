from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from core.deployment import Edition
from models.product.stock import Stock
from schemas.product.stock import validate_weight_grams_for_edition

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

def active_stocks_select() -> Select[tuple[Stock]]:
    return select(Stock).where(Stock.deleted_at.is_(None))

def count_active_stocks(db: Session) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(Stock).where(Stock.deleted_at.is_(None))
        )
        or 0
    )

def list_active_stocks(
    db: Session,
    *,
    page: int,
    limit: int,
    sort_by: str,
    sort_direction: str,
) -> tuple[list[Stock], int]:
    total = count_active_stocks(db)
    column = _SORT_COLUMNS[sort_by]
    order = column.asc() if sort_direction == "asc" else column.desc()
    statement = active_stocks_select().order_by(order)
    offset = (page - 1) * limit
    rows = list(db.scalars(statement.offset(offset).limit(limit)).all())
    return rows, total

def get_active_stock(db: Session, stock_id: UUID) -> Stock | None:
    return db.scalar(active_stocks_select().where(Stock.id == stock_id))

def coerce_weight_grams_for_edition(
    weight_grams: int | None,
    edition: Edition,
) -> int | None:
    return validate_weight_grams_for_edition(weight_grams, edition)
