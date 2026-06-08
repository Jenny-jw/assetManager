from typing import Any

from core.tea_pricing import line_total_value

SUMMARY_PROJECTION = {
    "_id": 0,
    "name": 1,
    "genre": 1,
    "origin": 1,
    "quantity": 1,
    "weight": 1,
    "price": 1,
}

def build_tea_summary(teas_collection) -> dict[str, Any]:
    total_assets = 0
    total_packages = 0
    total_weight_grams = 0
    total_value = 0
    by_origin: dict[str, int] = {}
    by_genre: dict[str, int] = {}

    for tea in teas_collection.find({}, SUMMARY_PROJECTION):
        if not isinstance(tea, dict):
            continue
        if "name" not in tea or "genre" not in tea:
            continue

        total_assets += 1
        quantity = tea.get("quantity") or 0
        weight = tea.get("weight") or 0
        price = tea.get("price")

        total_packages += quantity
        total_weight_grams += weight * quantity
        total_value += line_total_value(price, weight, quantity)

        origin = tea.get("origin") or "Unknown"
        genre = tea.get("genre") or "Unknown"
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