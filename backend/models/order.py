from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

class StockMovementReason(str, Enum):
    order = "order"
    adjustment = "adjustment"
    restock = "restock"

class OrderInDB(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    user_id: str
    status: OrderStatus
    total_amount: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime

class OrderItemInDB(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    order_id: ObjectId
    tea_id: str
    tea_name: str
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)
    line_total: int = Field(ge=0)
    created_at: datetime

class StockMovementInDB(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tea_id: str
    delta: int
    quantity_before: int = Field(ge=0)
    quantity_after: int = Field(ge=0)
    reason: StockMovementReason
    ref_type: str
    ref_id: str
    created_by: str
    created_at: datetime