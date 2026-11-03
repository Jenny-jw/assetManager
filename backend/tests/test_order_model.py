from datetime import datetime, timezone

import pytest
from bson import ObjectId
from pydantic import ValidationError

from models.order import OrderInDB, OrderItemInDB, OrderStatus, StockMovementInDB, StockMovementReason

def _now() -> datetime:
    return datetime.now(timezone.utc)

def test_reference_ids_are_hex_strings_and_primary_key_is_not_stored():
    now = _now()
    order_id = str(ObjectId())
    tea_id = str(ObjectId())
    user_id = str(ObjectId())
    order = OrderInDB(
        user_id=user_id,
        status=OrderStatus.pending,
        total_amount=600,
        created_at=now,
        updated_at=now,
    )
    item = OrderItemInDB(
        order_id=order_id,
        tea_id=tea_id,
        tea_name="Alishan",
        quantity=2,
        unit_price=300,
        line_total=600,
        created_at=now,
    )
    movement = StockMovementInDB(
        tea_id=tea_id,
        delta=-2,
        quantity_before=5,
        quantity_after=3,
        reason=StockMovementReason.order,
        ref_type="order",
        ref_id=order_id,
        created_by=user_id,
        created_at=now,
    )

    assert order.model_dump()["user_id"] == user_id
    assert item.model_dump()["order_id"] == order_id
    assert movement.model_dump()["ref_id"] == order_id
    assert "id" not in order.model_dump()

    with pytest.raises(ValidationError):
        OrderItemInDB(
            order_id=ObjectId(order_id),
            tea_id=tea_id,
            tea_name="Alishan",
            quantity=2,
            unit_price=300,
            line_total=600,
            created_at=now,
        )

    with pytest.raises(ValidationError):
        OrderInDB(
            user_id="someone-else",
            status=OrderStatus.pending,
            total_amount=0,
            created_at=now,
            updated_at=now,
        )