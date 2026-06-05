from enum import Enum

class OrderStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"

class StockMovementReason(str, Enum):
    order = "order"
    adjustment = "adjustment"
    restock = "restock"