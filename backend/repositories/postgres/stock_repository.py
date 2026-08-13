from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.stock import Stock

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

class StockRepository:
    """Tenant-scoped persistence for stocks. All reads/writes filter by tenant_id."""

    def __init__(self, db: Session, *, tenant_id: UUID) -> None:
        self._db = db
        self._tenant_id = tenant_id

    def _active_select(self) -> Select[tuple[Stock]]:
        return select(Stock).where(
            Stock.deleted_at.is_(None),
            Stock.tenant_id == self._tenant_id,
        )

    def _apply_list_filters(
        self,
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

    def get_active(self, stock_id: UUID) -> Stock | None:
        return self._db.scalar(self._active_select().where(Stock.id == stock_id))

    def list_all_active(self) -> list[Stock]:
        return list(self._db.scalars(self._active_select()).all())

    def count_active(self) -> int:
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(Stock)
                .where(
                    Stock.deleted_at.is_(None),
                    Stock.tenant_id == self._tenant_id,
                )
            )
            or 0
        )

    def list_active(
        self,
        *,
        page: int,
        limit: int,
        sort_by: str,
        sort_direction: str,
        search: str | None = None,
        genre: str | None = None,
        origin: str | None = None,
    ) -> tuple[list[Stock], int]:
        statement = self._apply_list_filters(
            self._active_select(),
            search=search,
            genre=genre,
            origin=origin,
        )
        total = int(
            self._db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
        column = _SORT_COLUMNS[sort_by]
        order = column.asc() if sort_direction == "asc" else column.desc()
        statement = statement.order_by(order)
        offset = (page - 1) * limit
        rows = list(self._db.scalars(statement.offset(offset).limit(limit)).all())
        return rows, total

    def create(self, **fields: object) -> Stock:
        stock = Stock(**fields, tenant_id=self._tenant_id)
        self._db.add(stock)
        self._db.commit()
        self._db.refresh(stock)
        return stock

    def update(self, stock: Stock, updates: dict[str, object]) -> Stock:
        for field, value in updates.items():
            setattr(stock, field, value)
        stock.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(stock)
        return stock

    def soft_delete(self, stock: Stock) -> None:
        now = datetime.now(timezone.utc)
        stock.deleted_at = now
        stock.updated_at = now
        self._db.commit()