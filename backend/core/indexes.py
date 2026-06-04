import logging

from core.db import db

logger = logging.getLogger(__name__)

def ensure_indexes() -> None:
    db.users.create_index("email", unique=True)
    db.teas.create_index([("genre", 1), ("created_at", -1)])
    db.teas.create_index([("origin", 1), ("created_at", -1)])
    db.teas.create_index([("name", "text"), ("producer", "text"), ("comment", "text")])
    logger.info("database indexes ensured")
