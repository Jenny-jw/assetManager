from datetime import datetime, timezone
from typing import Annotated
from pydantic import BaseModel, Field
from models.order import OrderStatus, StockMovementReason

Qty = Annotated[int, Field(ge=1, le=999)]

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class OrderItemCreate(BaseModel):
    tea_id: str
    quantity: Qty = Field(..., description="Number of packages to order")

class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)

class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    tea_id: str
    tea_name: str
    quantity: int = Field(..., description="Number of packages ordered")
    unit_price: int = Field(..., description="Price per package at time of order")
    line_total: int

class StockMovementResponse(BaseModel):
    id: str
    tea_id: str
    delta: int
    quantity_before: int
    quantity_after: int
    reason: StockMovementReason
    ref_type: str
    ref_id: str
    created_by: str
    created_at: datetime

class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: OrderStatus
    total_amount: int
    created_at: datetime
    items: list[OrderItemResponse] = []

class OrderListResponse(BaseModel):
    data: list[OrderResponse]
    total: int
