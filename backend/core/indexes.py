import logging

from core.db import db

logger = logging.getLogger(__name__)

def ensure_indexes() -> None:
    db.users.create_index("email", unique=True)
    db.teas.create_index([("genre", 1), ("created_at", -1)])
    db.teas.create_index([("origin", 1), ("created_at", -1)])
    db.teas.create_index([("name", "text"), ("producer", "text"), ("comment", "text")])
    db.orders.create_index([("user_id", 1), ("created_at", -1)])
    db.order_items.create_index("order_id")
    db.stock_movements.create_index([("tea_id", 1), ("created_at", -1)])
    db.stock_movements.create_index([("ref_type", 1), ("ref_id", 1)])
    logger.info("database indexes ensured")
