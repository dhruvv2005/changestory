import pytest
from changestory_sample.utils import format_currency, sanitize_string, normalize_code


def test_format_currency():
    assert format_currency(12.3456) == "$12.35"
    assert format_currency(0.0) == "$0.00"


def test_sanitize_string():
    assert sanitize_string("  Hello World  ") == "hello world"
    assert sanitize_string("") == ""


def test_normalize_code():
    assert normalize_code("  item-99  ") == "ITEM-99"
