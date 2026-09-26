import pytest
from changestory_sample.order_service import process_order, summarize_cart


def test_process_order():
    order = process_order(100.0, 0.10, "ORD-123")
    assert order["order_code"] == "ORD-123"
    assert order["total"] == 110.0
    assert order["total_formatted"] == "$110.00"


def test_summarize_cart():
    items = [{"price": 10.0}, {"price": 20.0}]
    cart = summarize_cart(items, 0.05)
    assert cart["count"] == 2
    # 10 + 0.5 = 10.5; 20 + 1.0 = 21.0; total = 31.5
    assert cart["grand_total"] == 31.5
