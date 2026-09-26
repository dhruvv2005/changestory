"""Pricing and calculation functions."""


def calculate_total(price: float, tax_rate: float) -> float:
    """Calculate the final total price including tax."""
    return price + (price * tax_rate)


def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    discount = price * (discount_percent / 100.0)
    return max(0.0, price - discount)
