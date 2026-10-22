"""Tests for login, token validation, and role enforcement."""


def test_login_with_valid_credentials(client, admin_user):
    response = client.post("/api/auth/login", json={"email": admin_user.email, "password": "testpass123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password(client, admin_user):
    response = client.post("/api/auth/login", json={"email": admin_user.email, "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_with_nonexistent_email(client):
    response = client.post("/api/auth/login", json={"email": "nobody@bizsync-tests.com", "password": "anything"})
    assert response.status_code == 401
    # Same message whether the email doesn't exist or the password was
    # wrong — see auth_service.py docstring for why this matters.
    assert response.json()["detail"] == "Incorrect email or password"


def test_protected_route_requires_token(client):
    response = client.get("/api/products")
    assert response.status_code == 401


def test_me_endpoint_returns_correct_identity(client, admin_headers, admin_user):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == admin_user.email
    assert body["role"] == "ADMIN"


def test_analyst_cannot_create_product(client, analyst_headers):
    """Role enforcement — ANALYST is read-only per the spec."""
    response = client.post(
        "/api/products", headers=analyst_headers,
        json={"product_code": "TEST001", "name": "Test", "category": "Test",
              "brand": "Test", "unit_price": 10, "cost_price": 5},
    )
    assert response.status_code == 403
