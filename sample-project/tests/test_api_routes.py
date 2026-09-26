import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from changestory_sample.api_routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_order_endpoint():
    response = client.get("/sample/order?price=200.0&tax_rate=0.08")
    assert response.status_code == 200
    data = response.json()
    assert data["order_code"] == "SAMPLE-ORD-1"
    assert data["total"] == 216.0
    assert data["total_formatted"] == "$216.00"


def test_format_endpoint():
    response = client.get("/sample/format?amount=99.9")
    assert response.status_code == 200
    assert response.json() == {"formatted": "$99.90"}
