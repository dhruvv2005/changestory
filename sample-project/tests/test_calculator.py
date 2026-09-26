import pytest
from changestory_sample.calculator import calculate_total, calculate_discount


def test_calculate_total():
    # 100 + 10% tax = 110.0
    result = calculate_total(100.0, 0.10)
    assert result == 110.0


def test_calculate_total_zero_tax():
    result = calculate_total(50.0, 0.0)
    assert result == 50.0


def test_calculate_discount():
    result = calculate_discount(100.0, 20.0)
    assert result == 80.0
