from fastapi import APIRouter, Depends, Query

from dependencies.auth import get_current_user, require_role
from models.order import OrderStatus
from models.user import UserRole
from schemas.order import OrderCreate, OrderListResponse, OrderResponse
from services.order_service import (
    approve_order,
    get_order_for_user,
    list_orders_for_user,
    place_order,
    reject_order,
)

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    payload: OrderCreate,
    current_user: dict = Depends(require_role(UserRole.user, UserRole.admin)),
):
    return place_order(payload, current_user)

@router.get("/", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(None, description="Filter by order status"),
    current_user: dict = Depends(get_current_user),
):
    return list_orders_for_user(
        current_user,
        page=page,
        limit=limit,
        status_filter=status.value if status else None,
    )

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    return get_order_for_user(order_id, current_user)

@router.patch("/{order_id}/approve", response_model=OrderResponse)
def approve_order_route(
    order_id: str,
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    return approve_order(order_id, current_user)

@router.patch("/{order_id}/reject", response_model=OrderResponse)
def reject_order_route(
    order_id: str,
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    return reject_order(order_id, current_user)
