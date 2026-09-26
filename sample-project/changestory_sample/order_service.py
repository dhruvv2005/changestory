"""Order processing service calling calculator and shared utilities."""

from changestory_sample.calculator import calculate_total
from changestory_sample.utils import format_currency


def process_order(price: float, tax_rate: float, order_code: str) -> dict:
    """Process an order by calculating total and formatting currency."""
    total = calculate_total(price, tax_rate)
    formatted = format_currency(total)
    return {
        "order_code": order_code,
        "total": total,
        "total_formatted": formatted,
    }


def summarize_cart(items: list[dict], tax_rate: float) -> dict:
    """Summarize an entire cart of items."""
    grand_total = 0.0
    for item in items:
        item_total = calculate_total(item["price"], tax_rate)
        grand_total += item_total
    return {
        "count": len(items),
        "grand_total": grand_total,
        "grand_total_formatted": format_currency(grand_total),
    }
