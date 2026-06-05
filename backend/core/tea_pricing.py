GRAMS_PER_JIN = 600

def price_per_package(price_per_jin: int, weight_grams: int) -> int:
    """Price for one package: (weight_g / 600) × price_per_jin."""
    return round((weight_grams / GRAMS_PER_JIN) * price_per_jin)