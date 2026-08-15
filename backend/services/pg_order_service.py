from __future__ import annotations

from uuid import UUID

from fastapi import status

from core.errors import ErrorCode, api_error
from core.tea_pricing import price_per_package
from models.order import Order, OrderItem, OrderStatus
from repositories.postgres.order_repository import OrderRepository
from repositories.postgres.stock_repository import StockRepository
from schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
)

def _parse_stock_id(raw: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_stock_id) from exc

def _availability_by_stock_id(
    items: list[OrderItem],
    stocks: StockRepository,
) -> dict[UUID, bool]:
    stock_ids = {item.stock_id for item in items}
    return {stock_id: stocks.get_active(stock_id) is not None for stock_id in stock_ids}

def serialize_order(
    order: Order,
    stocks: StockRepository,
) -> OrderResponse:
    available = _availability_by_stock_id(order.items, stocks)
    return OrderResponse(
        id=str(order.id),
        user_id=str(order.created_by),
        status=OrderStatus(order.status),
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                id=str(item.id),
                order_id=str(item.order_id),
                stock_id=str(item.stock_id),
                stock_name=item.stock_name,
                stock_available=available.get(item.stock_id, False),
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
            for item in order.items
        ],
    )

def create_owner_order(
    payload: OrderCreate,
    *,
    created_by: UUID,
    orders: OrderRepository,
    stocks: StockRepository,
) -> OrderResponse:
    line_specs: list[dict[str, object]] = []
    total_amount = 0
    for line in payload.items:
        stock_id = _parse_stock_id(line.stock_id)
        stock = stocks.get_active(stock_id)
        if stock is None:
            raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.stock_not_found)
        if stock.price_per_jin is None or stock.weight_grams is None:
            raise api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.stock_not_orderable)
        unit_price = price_per_package(stock.price_per_jin, stock.weight_grams)
        line_total = unit_price * line.quantity
        total_amount += line_total
        line_specs.append(
            {
                "stock_id": stock.id,
                "stock_name": stock.name,
                "quantity": line.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )
    order = orders.create(
        created_by=created_by,
        status=OrderStatus.pending,
        total_amount=total_amount,
        items=line_specs,
    )
    loaded = orders.get(order.id)
    if loaded is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.order_not_found)
    return serialize_order(loaded, stocks)

def list_owner_orders(
    *,
    page: int,
    limit: int,
    status_filter: OrderStatus | None,
    orders: OrderRepository,
    stocks: StockRepository,
) -> OrderListResponse:
    rows, total = orders.list(page=page, limit=limit, status=status_filter)
    return OrderListResponse(
        data=[serialize_order(order, stocks) for order in rows],
        total=total,
    )

def get_owner_order(
    order_id: UUID,
    *,
    orders: OrderRepository,
    stocks: StockRepository,
) -> OrderResponse:
    order = orders.get(order_id)
    if order is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.order_not_found)
    return serialize_order(order, stocks)