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
from services.stock_transactions import run_optional_transaction

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

def _require_admin(current_user: dict[str, Any]) -> None:
    if _normalize_role(current_user.get("role")) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

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

def _get_pending_order(order_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order id")

    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.get("status") != OrderStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order is not pending approval",
        )

    items = _load_order_items(order["_id"])
    if not items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order has no items",
        )

    return order, items

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
    status_filter: str | None = None,
) -> dict[str, Any]:
    role = _normalize_role(current_user.get("role"))
    filters: dict[str, Any] = {}

    if role != "admin":
        filters["user_id"] = current_user["id"]

    if status_filter:
        if status_filter not in {s.value for s in OrderStatus}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        filters["status"] = status_filter

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

def count_pending_orders() -> int:
    return db.orders.count_documents({"status": OrderStatus.pending.value})

def _build_line_specs(
    payload: OrderCreate,
    *,
    session: ClientSession | None = None,
) -> list[dict[str, Any]]:
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

    return line_specs

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

def _insert_order_items(
    order_oid: ObjectId,
    line_specs: list[dict[str, Any]],
    *,
    now: datetime,
    session: ClientSession | None = None,
) -> list[dict[str, Any]]:
    item_docs: list[dict[str, Any]] = []
    for spec in line_specs:
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
    return item_docs

def _rollback_order(order_oid: ObjectId, item_docs: list[dict[str, Any]]) -> None:
    db.order_items.delete_many({"order_id": order_oid})
    db.orders.delete_one({"_id": order_oid})

def _place_order_core(
    payload: OrderCreate,
    current_user: dict[str, Any],
    *,
    session: ClientSession | None = None,
) -> dict[str, Any]:
    user_id = current_user["id"]
    now = utcnow()
    line_specs = _build_line_specs(payload, session=session)
    total_amount = sum(spec["line_total"] for spec in line_specs)

    order_doc = {
        "user_id": user_id,
        "status": OrderStatus.pending.value,
        "total_amount": total_amount,
        "created_at": now,
        "updated_at": now,
    }
    order_insert = db.orders.insert_one(order_doc, session=session)
    order_oid = order_insert.inserted_id

    item_docs: list[dict[str, Any]] = []
    try:
        item_docs = _insert_order_items(order_oid, line_specs, now=now, session=session)
    except Exception:
        if session is None:
            _rollback_order(order_oid, item_docs)
        raise

    order_doc["_id"] = order_oid
    logger.info(
        "order submitted for approval",
        extra={
            "order_id": str(order_oid),
            "user_id": user_id,
            "total_amount": total_amount,
            "line_count": len(item_docs),
        },
    )
    return _serialize_order(order_doc, item_docs)

def _claim_pending_order(
    order_oid: ObjectId,
    *,
    session: ClientSession | None = None,
) -> dict[str, Any]:
    """Atomically move pending → confirmed so the same order cannot be fulfilled twice."""
    claimed = db.orders.find_one_and_update(
        {"_id": order_oid, "status": OrderStatus.pending.value},
        {"$set": {"status": OrderStatus.confirmed.value, "updated_at": utcnow()}},
        return_document=ReturnDocument.BEFORE,
        session=session,
    )
    if not claimed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order is not pending approval",
        )
    return claimed

def _rollback_fulfillment(
    order_oid: ObjectId,
    applied: list[tuple[ObjectId, int]],
) -> None:
    """Compensating rollback when Mongo transactions are off (tests / standalone Mongo)."""
    for tea_oid, quantity in reversed(applied):
        db.teas.update_one(
            {"_id": tea_oid},
            {"$inc": {"quantity": quantity}},
        )
    db.stock_movements.delete_many({"ref_type": "order", "ref_id": str(order_oid)})
    db.orders.update_one(
        {"_id": order_oid},
        {"$set": {"status": OrderStatus.pending.value, "updated_at": utcnow()}},
    )

def _fulfill_pending_order(
    order: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    actor_id: str,
    session: ClientSession | None = None,
) -> None:
    """
    Transaction-safe stock deduction on admin approve:
      1. Claim order (pending → confirmed) — prevents double-approve
      2. Per line: atomic decrement only if quantity >= ordered qty
      3. Insert stock_movements audit row per line
    """
    now = utcnow()
    order_oid = order["_id"]
    _claim_pending_order(order_oid, session=session)

    applied: list[tuple[ObjectId, int]] = []
    try:
        for item in items:
            tea_oid = ObjectId(item["tea_id"])
            tea_before = _reserve_tea_stock(
                tea_oid, item["quantity"], session=session
            )
            applied.append((tea_oid, item["quantity"]))
            qty_before = tea_before["quantity"]
            qty_after = qty_before - item["quantity"]

            movement_doc = {
                "tea_id": item["tea_id"],
                "delta": -item["quantity"],
                "quantity_before": qty_before,
                "quantity_after": qty_after,
                "reason": StockMovementReason.order.value,
                "ref_type": "order",
                "ref_id": str(order_oid),
                "created_by": actor_id,
                "created_at": now,
            }
            db.stock_movements.insert_one(movement_doc, session=session)
    except Exception:
        if session is None:
            _rollback_fulfillment(order_oid, applied)
        raise

def approve_order(order_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
    _require_admin(current_user)
    order, items = _get_pending_order(order_id)

    def _approve(session: ClientSession | None) -> None:
        _fulfill_pending_order(
            order,
            items,
            actor_id=current_user["id"],
            session=session,
        )

    try:
        run_optional_transaction(enabled=_use_transactions(), operation=_approve)
    except HTTPException:
        raise
    except Exception as exc:
        if _use_transactions():
            logger.warning("transactional approve failed, retrying without session: %s", exc)
            order, items = _get_pending_order(order_id)
            _approve(None)
        else:
            raise

    logger.info(
        "order approved",
        extra={"order_id": order_id, "admin_id": current_user["id"]},
    )

    updated = db.orders.find_one({"_id": ObjectId(order_id)})
    updated_items = _load_order_items(updated["_id"])
    return _serialize_order(updated, updated_items)

def reject_order(order_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
    _require_admin(current_user)
    order, items = _get_pending_order(order_id)
    now = utcnow()

    db.orders.update_one(
        {"_id": order["_id"]},
        {"$set": {"status": OrderStatus.cancelled.value, "updated_at": now}},
    )

    logger.info(
        "order rejected",
        extra={"order_id": order_id, "admin_id": current_user["id"]},
    )

    updated = db.orders.find_one({"_id": order["_id"]})
    return _serialize_order(updated, items)

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
