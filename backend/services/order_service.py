from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.client_session import ClientSession

from core.db import client, db
from core.tea_pricing import price_per_package
from models.order import OrderStatus, StockMovementReason
from schemas.order import OrderCreate

logger = logging.getLogger(__name__)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _use_transactions() -> bool:
    return os.getenv("USE_DB_TRANSACTIONS", "true").strip().lower() in {
        "1",
        "true",
        "yes",
    }

def _normalize_role(role: Any) -> str:
    return role.value if hasattr(role, "value") else str(role)

def _serialize_order(
    order_doc: dict[str, Any],
    item_docs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": str(order_doc["_id"]),
        "user_id": order_doc["user_id"],
        "status": order_doc["status"],
        "total_amount": order_doc["total_amount"],
        "created_at": order_doc["created_at"],
        "items": [
            {
                "id": str(item["_id"]),
                "order_id": str(item["order_id"]),
                "tea_id": item["tea_id"],
                "tea_name": item["tea_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "line_total": item["line_total"],
            }
            for item in item_docs
        ],
    }

def _load_order_items(order_id: ObjectId) -> list[dict[str, Any]]:
    return list(db.order_items.find({"order_id": order_id}))

def get_order_for_user(order_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order id")

    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    role = _normalize_role(current_user.get("role"))
    if role != "admin" and order["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    items = _load_order_items(order["_id"])
    return _serialize_order(order, items)

def list_orders_for_user(
    current_user: dict[str, Any],
    *,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    role = _normalize_role(current_user.get("role"))
    filters: dict[str, Any] = {}
    if role != "admin":
        filters["user_id"] = current_user["id"]

    skip = (page - 1) * limit
    total = db.orders.count_documents(filters)
    orders = list(
        db.orders.find(filters).sort("created_at", -1).skip(skip).limit(limit)
    )

    data = []
    for order in orders:
        items = _load_order_items(order["_id"])
        data.append(_serialize_order(order, items))

    return {"data": data, "total": total}

def _reserve_tea_stock(
    tea_oid: ObjectId,
    quantity: int,
    *,
    session: ClientSession | None = None,
) -> dict[str, Any]:
    tea = db.teas.find_one_and_update(
        {"_id": tea_oid, "quantity": {"$gte": quantity}},
        {
            "$inc": {"quantity": -quantity},
            "$set": {"updated_at": utcnow()},
        },
        return_document=ReturnDocument.BEFORE,
        session=session,
    )
    if not tea:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock for one or more items",
        )

    current_qty = tea.get("quantity")
    if current_qty is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tea is not available for ordering",
        )

    return tea

def _place_order_core(
    payload: OrderCreate,
    current_user: dict[str, Any],
    *,
    session: ClientSession | None = None,
) -> dict[str, Any]:
    user_id = current_user["id"]
    now = utcnow()
    line_specs: list[dict[str, Any]] = []

    for line in payload.items:
        if not ObjectId.is_valid(line.tea_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tea id: {line.tea_id}",
            )

        tea_oid = ObjectId(line.tea_id)
        tea = db.teas.find_one({"_id": tea_oid}, session=session)
        if not tea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tea not found: {line.tea_id}",
            )

        price_per_jin = tea.get("price")
        if price_per_jin is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tea '{tea.get('name')}' has no price and cannot be ordered",
            )

        weight_grams = tea.get("weight")
        if weight_grams is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tea '{tea.get('name')}' has no package weight and cannot be ordered",
            )

        unit_price = price_per_package(price_per_jin, weight_grams)

        quantity_available = tea.get("quantity")
        if quantity_available is None or quantity_available < line.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for '{tea.get('name')}'",
            )

        line_specs.append(
            {
                "tea_oid": tea_oid,
                "tea_id": line.tea_id,
                "tea_name": tea["name"],
                "quantity": line.quantity,
                "unit_price": unit_price,
                "line_total": unit_price * line.quantity,
            }
        )

    total_amount = sum(spec["line_total"] for spec in line_specs)
    order_doc = {
        "user_id": user_id,
        "status": OrderStatus.confirmed.value,
        "total_amount": total_amount,
        "created_at": now,
        "updated_at": now,
    }
    order_insert = db.orders.insert_one(order_doc, session=session)
    order_oid = order_insert.inserted_id

    item_docs: list[dict[str, Any]] = []
    try:
        for spec in line_specs:
            tea_before = _reserve_tea_stock(
                spec["tea_oid"], spec["quantity"], session=session
            )
            qty_before = tea_before["quantity"]
            qty_after = qty_before - spec["quantity"]

            movement_doc = {
                "tea_id": spec["tea_id"],
                "delta": -spec["quantity"],
                "quantity_before": qty_before,
                "quantity_after": qty_after,
                "reason": StockMovementReason.order.value,
                "ref_type": "order",
                "ref_id": str(order_oid),
                "created_by": user_id,
                "created_at": now,
            }
            db.stock_movements.insert_one(movement_doc, session=session)

            item_doc = {
                "order_id": order_oid,
                "tea_id": spec["tea_id"],
                "tea_name": spec["tea_name"],
                "quantity": spec["quantity"],
                "unit_price": spec["unit_price"],
                "line_total": spec["line_total"],
                "created_at": now,
            }
            item_insert = db.order_items.insert_one(item_doc, session=session)
            item_doc["_id"] = item_insert.inserted_id
            item_docs.append(item_doc)
    except Exception:
        if session is None:
            _rollback_order(order_oid, item_docs)
        raise

    order_doc["_id"] = order_oid
    logger.info(
        "order placed",
        extra={
            "order_id": str(order_oid),
            "user_id": user_id,
            "total_amount": total_amount,
            "line_count": len(item_docs),
        },
    )
    return _serialize_order(order_doc, item_docs)

def _rollback_order(order_oid: ObjectId, item_docs: list[dict[str, Any]]) -> None:
    for item in item_docs:
        db.teas.update_one(
            {"_id": ObjectId(item["tea_id"])},
            {"$inc": {"quantity": item["quantity"]}},
        )
    db.stock_movements.delete_many({"ref_type": "order", "ref_id": str(order_oid)})
    db.order_items.delete_many({"order_id": order_oid})
    db.orders.delete_one({"_id": order_oid})

def _place_order_transactional(
    payload: OrderCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    with client.start_session() as session:
        with session.start_transaction():
            return _place_order_core(payload, current_user, session=session)

def place_order(payload: OrderCreate, current_user: dict[str, Any]) -> dict[str, Any]:
    role = _normalize_role(current_user.get("role"))
    if role == "guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guests cannot place orders",
        )

    if _use_transactions():
        try:
            return _place_order_transactional(payload, current_user)
        except Exception as exc:
            logger.warning("transactional order failed, retrying sequential: %s", exc)

    return _place_order_core(payload, current_user, session=None)