GRAMS_PER_JIN = 600

def price_per_package(price_per_jin: int, weight_grams: int) -> int:
    """Price for one package: (weight_g / 600) × price_per_jin."""
    return round((weight_grams / GRAMS_PER_JIN) * price_per_jin)

def line_total_value(
    price_per_jin: int | None,
    weight_grams: int | None,
    quantity: int | None,
) -> int:
    """Inventory line total: price per package × number of packages."""
    if price_per_jin is None or weight_grams is None or quantity is None:
        return 0
    return price_per_package(price_per_jin, weight_grams) * quantity