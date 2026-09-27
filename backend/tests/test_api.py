from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DATABASE_URL"] = "sqlite:///./test_wisebar.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEBUG"] = "true"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-pass"
os.environ["CORS_ORIGINS"] = "http://test"

db_path = os.path.join(os.path.dirname(__file__), "..", "test_wisebar.db")
if os.path.exists(db_path):
    os.remove(db_path)

from app.config import get_settings

get_settings.cache_clear()

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test:
        session = test.get("/api/session")
        assert session.status_code == 200
        token = session.json()["csrf"]
        test.headers.update({"X-CSRF-Token": token})
        yield test


def test_health(client):
    assert client.get("/api/health").json()["ok"] is True


def test_products_have_no_invented_nutrition_or_price(client):
    rows = client.get("/api/products").json()
    assert len(rows) >= 5
    for row in rows:
        assert row["price_inr"] is None
        assert row["nutrition"]["protein_g"] is None
        assert row["nutrition"]["status"] == "pending_verification"
        assert row["purchasable"] is False
        assert row["review_count"] == 0
        assert row["lab_report_url"] is None


def test_search_injection_is_safe(client):
    response = client.get("/api/search", params={"q": "' OR 1=1 --"})
    assert response.status_code == 200
    assert isinstance(response.json()["products"], list)


def test_cannot_add_unverified_product_to_cart(client):
    product = client.get("/api/products").json()[0]
    response = client.post("/api/cart/items", json={"product_id": product["id"], "quantity": 1})
    assert response.status_code == 409


def test_checkout_blocked(client):
    response = client.post(
        "/api/orders/checkout",
        json={"name": "Asha Rao", "phone": "9876543210", "email": "asha@example.com", "address": "12 Residency Road", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"},
    )
    assert response.status_code == 409


def test_admin_requires_auth(client):
    assert client.get("/api/admin/dashboard").status_code == 401


def test_admin_login_and_cannot_publish_incomplete_product(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-pass"})
    assert login.status_code == 200
    assert login.json()["role"] == "admin"
    product = client.get("/api/admin/products").json()[0]
    product["purchasable"] = True
    product["available"] = 10
    response = client.patch(f"/api/admin/products/{product['id']}", json=_product_body(product))
    assert response.status_code == 400
    assert "missing" in response.json()["detail"]


def test_corporate_lead_validation(client):
    bad = client.post("/api/corporate/leads", json={"company": "Acme", "name": "Riya", "email": "not-an-email", "phone": "9876543210", "employee_count": "40", "requirement": "Pantry", "expected_quantity": "100", "message": "Need a quote for the office pantry."})
    assert bad.status_code == 422
    ok = client.post("/api/corporate/leads", json={"company": "Acme", "name": "Riya", "email": "riya@acme.example", "phone": "9876543210", "employee_count": "40", "requirement": "Pantry", "expected_quantity": "100", "message": "Need a quote for the office pantry."})
    assert ok.status_code == 200


def test_recommendations_use_catalogue_only(client):
    response = client.post("/api/recommendations", json={"occasion": "morning", "taste": "grain", "protein": "20-30", "budget": "100-200"})
    assert response.status_code == 200
    body = response.json()
    assert body["notes"]
    slugs = {row["slug"] for row in body["products"]}
    assert "classic-grain-muesli" in slugs


def test_webhook_without_secret(client):
    assert client.post("/api/payments/webhook", json={"event": "payment.captured"}).status_code == 503


def test_sitemap(client):
    response = client.get("/api/sitemap.xml")
    assert response.status_code == 200
    assert "/products/cocoa-crunch-bar" in response.text


def test_register_and_me(client):
    created = client.post("/api/auth/register", json={"name": "Neel Shah", "email": "neel@example.com", "password": "a-long-password"})
    assert created.status_code == 200
    me = client.get("/api/auth/me")
    assert me.json()["email"] == "neel@example.com"


def _product_body(product: dict) -> dict:
    return {
        "sku": product["sku"],
        "slug": product["slug"],
        "name": product["name"],
        "flavor": product["flavor"],
        "flavor_family": product["flavor_family"],
        "category_slug": product["category_slug"],
        "description": product["description"],
        "status": product["status"],
        "purchasable": True,
        "is_featured": product["is_featured"],
        "sort_order": 1,
        "occasions": product["occasions"],
        "dietary_labels": [],
        "available": 10,
    }
