"""Tests for product creation and duplicate-code rejection."""


def test_create_product(client, admin_headers):
    response = client.post(
        "/api/products", headers=admin_headers,
        json={"product_code": "TEST001", "name": "Test Product", "category": "Snacks",
              "brand": "TestBrand", "unit_price": 50.0, "cost_price": 30.0, "reorder_level": 20},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["product_code"] == "TEST001"
    assert body["active"] is True


def test_duplicate_product_code_rejected(client, admin_headers):
    payload = {"product_code": "TEST002", "name": "First", "category": "Snacks",
               "brand": "TestBrand", "unit_price": 50.0, "cost_price": 30.0}
    first = client.post("/api/products", headers=admin_headers, json=payload)
    assert first.status_code == 201

    payload["name"] = "Duplicate Attempt"
    second = client.post("/api/products", headers=admin_headers, json=payload)
    assert second.status_code == 409


def test_negative_price_rejected_by_validation(client, admin_headers):
    response = client.post(
        "/api/products", headers=admin_headers,
        json={"product_code": "TEST003", "name": "Bad Price", "category": "Snacks",
              "brand": "TestBrand", "unit_price": -10, "cost_price": 30},
    )
    # Pydantic's Field(gt=0) rejects this before it ever reaches the
    # database — a 422, not a 500 or a silently-accepted bad row.
    assert response.status_code == 422


def test_get_nonexistent_product_returns_404(client, admin_headers):
    response = client.get("/api/products/999999", headers=admin_headers)
    assert response.status_code == 404


def test_deactivate_product(client, admin_headers):
    create_resp = client.post(
        "/api/products", headers=admin_headers,
        json={"product_code": "TEST004", "name": "To Deactivate", "category": "Snacks",
              "brand": "TestBrand", "unit_price": 50.0, "cost_price": 30.0},
    )
    product_id = create_resp.json()["id"]

    deactivate_resp = client.delete(f"/api/products/{product_id}", headers=admin_headers)
    assert deactivate_resp.status_code == 200

    get_resp = client.get(f"/api/products/{product_id}", headers=admin_headers)
    assert get_resp.json()["active"] is False
