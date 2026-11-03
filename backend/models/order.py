from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

def assert_object_id_hex(value: str) -> str:
    if not isinstance(value, str) or len(value) != 24:
        raise ValueError("reference id must be a 24-character hex string")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError("reference id must be a 24-character hex string")
    return value

ObjectIdHex = Annotated[str, AfterValidator(assert_object_id_hex)]

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

    user_id: ObjectIdHex
    status: OrderStatus
    total_amount: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime

class OrderItemInDB(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    order_id: ObjectIdHex
    tea_id: ObjectIdHex
    tea_name: str
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)
    line_total: int = Field(ge=0)
    created_at: datetime

class StockMovementInDB(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tea_id: ObjectIdHex
    delta: int
    quantity_before: int = Field(ge=0)
    quantity_after: int = Field(ge=0)
    reason: StockMovementReason
    ref_type: str
    ref_id: ObjectIdHex
    created_by: ObjectIdHex
    created_at: datetime