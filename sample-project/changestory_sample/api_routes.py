"""API routes and handlers for sample service."""

from fastapi import APIRouter
from changestory_sample.order_service import process_order
from changestory_sample.utils import format_currency

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("/order")
def get_order_endpoint(price: float = 100.0, tax_rate: float = 0.05):
    """Endpoint to calculate and format order details."""
    result = process_order(price, tax_rate, "SAMPLE-ORD-1")
    return result


@router.get("/format")
def format_endpoint(amount: float = 50.0):
    """Endpoint to format arbitrary currency."""
    formatted = format_currency(amount)
    return {"formatted": formatted}
