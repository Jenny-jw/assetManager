from __future__ import annotations

import pytest

from core.deployment import Edition
from services.stock_queries import coerce_weight_grams_for_edition

def test_coerce_weight_grams_personal_allows_75_and_150():
    assert coerce_weight_grams_for_edition(75, Edition.personal) == 75
    assert coerce_weight_grams_for_edition(150, Edition.personal) == 150

def test_coerce_weight_grams_personal_rejects_other_values():
    with pytest.raises(ValueError, match="75 or 150"):
        coerce_weight_grams_for_edition(100, Edition.personal)

def test_coerce_weight_grams_professional_allows_positive():
    assert coerce_weight_grams_for_edition(100, Edition.professional) == 100

def test_coerce_weight_grams_none_passes_through():
    assert coerce_weight_grams_for_edition(None, Edition.personal) is None