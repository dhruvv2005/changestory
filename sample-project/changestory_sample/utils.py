"""Shared utility functions used across multiple services."""


def format_currency(amount: float) -> str:
    """Format a monetary amount to a standard currency string."""
    return f"${amount:0.2f}"


def sanitize_string(value: str) -> str:
    """Strip whitespace and lower case string for standard processing."""
    if not value:
        return ""
    return value.strip().lower()


def normalize_code(code: str) -> str:
    """Normalize item or order code."""
    sanitized = sanitize_string(code)
    return sanitized.upper()
