from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.order import OrderStatus, StockMovementReason

Qty = Annotated[int, Field(ge=1, le=999)]

class OrderItemCreate(BaseModel):
    stock_id: str
    quantity: Qty = Field(..., description="Number of packages to order")

class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    stock_id: str
    stock_name: str
    stock_available: bool = True
    quantity: int = Field(..., description="Number of packages ordered")
    unit_price: int = Field(..., description="Price per package at time of order")
    line_total: int

    @field_validator("id", "order_id", "stock_id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        return str(value)

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stock_id: str
    delta: int
    quantity_before: int
    quantity_after: int
    reason: StockMovementReason
    ref_type: str
    ref_id: str
    created_by: str
    created_at: datetime

    @field_validator("id", "stock_id", "ref_id", "created_by", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        return str(value)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: OrderStatus
    total_amount: int
    created_at: datetime
    items: list[OrderItemResponse] = []

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        if isinstance(value, UUID):
            return str(value)
        return str(value)

class OrderListResponse(BaseModel):
    data: list[OrderResponse]
    total: int