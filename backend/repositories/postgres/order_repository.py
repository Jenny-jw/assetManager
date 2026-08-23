from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, selectinload

from models.order import Order, OrderItem, OrderStatus, StockMovement

class OrderRepository:
    """Tenant-scoped persistence for orders and stock movements."""

    def __init__(self, db: Session, *, tenant_id: UUID) -> None:
        self._db = db
        self._tenant_id = tenant_id

    def _order_select(self) -> Select[tuple[Order]]:
        return (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.tenant_id == self._tenant_id)
        )

    def get(self, order_id: UUID) -> Order | None:
        return self._db.scalar(self._order_select().where(Order.id == order_id))

    def list(
        self,
        *,
        page: int,
        limit: int,
        status: OrderStatus | str | None = None,
    ) -> tuple[list[Order], int]:
        statement = self._order_select()
        if status is not None:
            status_value = status.value if isinstance(status, OrderStatus) else status
            statement = statement.where(Order.status == status_value)
        total = int(
            self._db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
        statement = statement.order_by(Order.created_at.desc())
        offset = (page - 1) * limit
        rows = list(self._db.scalars(statement.offset(offset).limit(limit)).all())
        return rows, total

    def create(
        self,
        *,
        created_by: UUID,
        status: OrderStatus | str,
        total_amount: int,
        items: Sequence[dict[str, object]],
    ) -> Order:
        status_value = status.value if isinstance(status, OrderStatus) else status
        order = Order(
            tenant_id=self._tenant_id,
            created_by=created_by,
            status=status_value,
            total_amount=total_amount,
            items=[
                OrderItem(
                    tenant_id=self._tenant_id,
                    stock_id=item["stock_id"],
                    stock_name=item["stock_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    line_total=item["line_total"],
                )
                for item in items
            ],
        )
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def add_movement(
        self,
        *,
        stock_id: UUID,
        delta: int,
        quantity_before: int,
        quantity_after: int,
        reason: str,
        ref_type: str,
        ref_id: UUID,
        created_by: UUID,
        commit: bool = True,
    ) -> StockMovement:
        movement = StockMovement(
            tenant_id=self._tenant_id,
            stock_id=stock_id,
            delta=delta,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
            created_by=created_by,
        )
        self._db.add(movement)
        if commit:
            self._db.commit()
            self._db.refresh(movement)
        else:
            self._db.flush()
        return movement

    def claim_pending(
        self,
        order_id: UUID,
        *,
        new_status: OrderStatus,
    ) -> Order | None:
        """Move pending → ``new_status`` for this tenant. Flush only; caller commits."""
        result = self._db.execute(
            update(Order)
            .where(
                Order.id == order_id,
                Order.tenant_id == self._tenant_id,
                Order.status == OrderStatus.pending.value,
            )
            .values(
                status=new_status.value,
                updated_at=datetime.now(timezone.utc),
            )
        )
        if result.rowcount != 1:
            return None
        order = self.get(order_id)
        if order is not None:
            self._db.refresh(order)
        return order

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def list_movements_for_ref(
        self,
        *,
        ref_type: str,
        ref_id: UUID,
    ) -> list[StockMovement]:
        statement = select(StockMovement).where(
            StockMovement.tenant_id == self._tenant_id,
            StockMovement.ref_type == ref_type,
            StockMovement.ref_id == ref_id,
        )
        return list(self._db.scalars(statement).all())