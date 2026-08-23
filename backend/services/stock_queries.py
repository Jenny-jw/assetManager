from __future__ import annotations

from core.deployment import Edition
from schemas.stock import validate_weight_grams_for_edition

def coerce_weight_grams_for_edition(
    weight_grams: int | None,
    edition: Edition,
) -> int | None:
    return validate_weight_grams_for_edition(weight_grams, edition)