from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from core.deployment import Edition
from models.product.stock import Stock
from schemas.product.stock import validate_weight_grams_for_edition

def active_stocks_select() -> Select[tuple[Stock]]:
    return select(Stock).where(Stock.deleted_at.is_(None))

def get_active_stock(db: Session, stock_id: UUID) -> Stock | None:
    return db.scalar(active_stocks_select().where(Stock.id == stock_id))

def coerce_weight_grams_for_edition(
    weight_grams: int | None,
    edition: Edition,
) -> int | None:
    return validate_weight_grams_for_edition(weight_grams, edition)
