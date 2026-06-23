from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from core.tea_pricing import line_total_value
from services.product.stock_queries import active_stocks_select

def build_stock_summary(db: Session) -> dict[str, Any]:
    total_assets = 0
    total_packages = 0
    total_weight_grams = 0
    total_value = 0
    by_origin: dict[str, int] = {}
    by_genre: dict[str, int] = {}

    for stock in db.scalars(active_stocks_select()).all():
        total_assets += 1
        quantity = stock.quantity or 0
        weight_grams = stock.weight_grams or 0

        total_packages += quantity
        total_weight_grams += weight_grams * quantity
        total_value += line_total_value(stock.price_per_jin, stock.weight_grams, stock.quantity)

        origin = stock.origin or "Unknown"
        genre = stock.genre or "Unknown"
        by_origin[origin] = by_origin.get(origin, 0) + 1
        by_genre[genre] = by_genre.get(genre, 0) + 1

    return {
        "total_assets": total_assets,
        "total_packages": total_packages,
        "total_weight_grams": total_weight_grams,
        "total_value": total_value,
        "by_origin": by_origin,
        "by_genre": by_genre,
    }
