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

def test_existing_order_item_order_ids_are_converted_once(fake_db):
    from services.order_service import convert_order_item_order_ids

    legacy_order_id = ObjectId()
    legacy_item_id = ObjectId()
    current_order_id = str(ObjectId())
    current_item_id = ObjectId()
    fake_db.order_items.docs[legacy_item_id] = {
        "_id": legacy_item_id,
        "order_id": legacy_order_id,
    }
    fake_db.order_items.docs[current_item_id] = {
        "_id": current_item_id,
        "order_id": current_order_id,
    }

    assert convert_order_item_order_ids(fake_db.order_items) == 1
    assert fake_db.order_items.docs[legacy_item_id]["order_id"] == str(legacy_order_id)
    assert isinstance(fake_db.order_items.docs[legacy_item_id]["_id"], ObjectId)
    assert fake_db.order_items.docs[current_item_id]["order_id"] == current_order_id
    assert convert_order_item_order_ids(fake_db.order_items) == 0