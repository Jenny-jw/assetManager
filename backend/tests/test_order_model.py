from datetime import datetime, timezone

import pytest
from bson import ObjectId
from pydantic import ValidationError

from models.order import OrderInDB, OrderItemInDB, OrderStatus, StockMovementInDB, StockMovementReason

def _now() -> datetime:
    return datetime.now(timezone.utc)

def test_order_models_match_the_fields_written_today():
    now = _now()
    order_id = ObjectId()
    order = OrderInDB(
        user_id="abc",
        status=OrderStatus.pending,
        total_amount=600,
        created_at=now,
        updated_at=now,
    )
    item = OrderItemInDB(
        order_id=order_id,
        tea_id="tea",
        tea_name="Alishan",
        quantity=2,
        unit_price=300,
        line_total=600,
        created_at=now,
    )
    movement = StockMovementInDB(
        tea_id="tea",
        delta=-2,
        quantity_before=5,
        quantity_after=3,
        reason=StockMovementReason.order,
        ref_type="order",
        ref_id=str(order_id),
        created_by="admin",
        created_at=now,
    )

    assert order.model_dump()["status"] == "pending"
    assert item.model_dump()["order_id"] == order_id
    assert movement.model_dump()["reason"] == "order"
    assert "id" not in order.model_dump()

    with pytest.raises(ValidationError):
        OrderItemInDB(
            order_id=order_id,
            tea_id="tea",
            tea_name="Alishan",
            quantity=0,
            unit_price=300,
            line_total=0,
            created_at=now,
        )