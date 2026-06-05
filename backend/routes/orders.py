from fastapi import APIRouter, Depends, Query

from dependencies.auth import get_current_user, require_role
from models.user import UserRole
from schemas.order import OrderCreate, OrderListResponse, OrderResponse
from services.order_service import place_order, list_orders_for_user, get_order_for_user

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
    current_user: dict = Depends(get_current_user),
):
    return list_orders_for_user(current_user, page=page, limit=limit)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    return get_order_for_user(order_id, current_user)