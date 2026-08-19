from core.tea_pricing import (
    GRAMS_PER_JIN,
    line_total_value,
    line_unrealized_profit,
    price_per_package,
)

def test_grams_per_jin():
    assert GRAMS_PER_JIN == 600

def test_price_per_package():
    assert price_per_package(1200, 150) == 300
    assert price_per_package(1200, 75) == 150

def test_line_total_value():
    assert line_total_value(1200, 150, 3) == 900
    assert line_total_value(None, 150, 3) == 0

def test_line_unrealized_profit():
    assert line_unrealized_profit(1200, 800, 150, 2) == 200
    assert line_unrealized_profit(1200, None, 150, 2) is None