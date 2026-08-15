from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core.capabilities import require_module
from core.errors import ErrorCode, api_error
from dependencies.auth import get_current_user, require_owner
from dependencies.repositories import get_order_repository, get_stock_repository
from models.order import OrderStatus
from repositories.postgres.order_repository import OrderRepository
from repositories.postgres.stock_repository import StockRepository
from schemas.order import OrderCreate, OrderListResponse, OrderResponse
from services.pg_order_service import (
    create_owner_order,
    get_owner_order,
    list_owner_orders,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(require_module("orders")), Depends(require_owner())],
)

def _parse_order_id(order_id: str) -> UUID:
    try:
        return UUID(order_id)
    except ValueError as exc:
        raise api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_order_id) from exc

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    current_user: dict = Depends(get_current_user),
    orders: OrderRepository = Depends(get_order_repository),
    stocks: StockRepository = Depends(get_stock_repository),
):
    return create_owner_order(
        payload,
        created_by=UUID(str(current_user["id"])),
        orders=orders,
        stocks=stocks,
    )

@router.get("/", response_model=OrderListResponse)
def list_orders(
    orders: OrderRepository = Depends(get_order_repository),
    stocks: StockRepository = Depends(get_stock_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(
        None,
        alias="status",
        description="Filter by order status",
    ),
):
    return list_owner_orders(
        page=page,
        limit=limit,
        status_filter=status_filter,
        orders=orders,
        stocks=stocks,
    )

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    orders: OrderRepository = Depends(get_order_repository),
    stocks: StockRepository = Depends(get_stock_repository),
):
    return get_owner_order(
        _parse_order_id(order_id),
        orders=orders,
        stocks=stocks,
    )