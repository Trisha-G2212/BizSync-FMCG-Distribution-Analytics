"""
Order and inventory tests — covering the transaction-safety logic that
is the most business-critical part of the whole application.
"""
import pytest
from app.models.distributor import Distributor
from app.models.retailer import Retailer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.enums import DistributorStatus, RetailerStatus


@pytest.fixture()
def order_fixtures(db_session):
    """A distributor, retailer, product, and a known inventory level —
    the minimum setup every order test needs."""
    distributor = Distributor(
        distributor_code="TESTDIST", name="Test Distributor", contact_person="Test",
        phone="1234567890", email="test@dist.test", city="Test City", state="Test State",
        status=DistributorStatus.ACTIVE,
    )
    db_session.add(distributor)
    db_session.flush()

    retailer = Retailer(
        retailer_code="TESTRET", name="Test Retailer", owner_name="Test Owner",
        phone="1234567890", city="Test City", state="Test State",
        distributor_id=distributor.id, status=RetailerStatus.ACTIVE,
    )
    db_session.add(retailer)

    product = Product(
        product_code="TESTPROD", name="Test Product", category="Snacks",
        brand="TestBrand", unit_price=100.0, cost_price=60.0, reorder_level=10,
    )
    db_session.add(product)
    db_session.flush()

    inventory = Inventory(product_id=product.id, distributor_id=distributor.id, quantity=10, reserved_quantity=0)
    db_session.add(inventory)
    db_session.commit()

    return {"distributor": distributor, "retailer": retailer, "product": product, "inventory": inventory}


def test_create_order(client, admin_headers, order_fixtures):
    response = client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": order_fixtures["retailer"].id,
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 5}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert float(body["total_amount"]) == 500.0  # 5 units * 100.0 unit_price


def test_order_creation_does_not_touch_inventory(client, admin_headers, order_fixtures, db_session):
    """Placing an order is just a request — inventory should be
    untouched until the order is actually CONFIRMED."""
    client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": order_fixtures["retailer"].id,
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 5}],
        },
    )
    db_session.refresh(order_fixtures["inventory"])
    assert order_fixtures["inventory"].quantity == 10  # unchanged


def test_confirm_order_with_sufficient_inventory(client, admin_headers, order_fixtures, db_session):
    order_resp = client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": order_fixtures["retailer"].id,
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 5}],
        },
    )
    order_id = order_resp.json()["id"]

    confirm_resp = client.patch(f"/api/orders/{order_id}/status", headers=admin_headers, json={"status": "CONFIRMED"})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    db_session.refresh(order_fixtures["inventory"])
    assert order_fixtures["inventory"].quantity == 5  # 10 - 5


def test_confirm_order_with_insufficient_inventory_is_rejected(client, admin_headers, order_fixtures, db_session):
    """THE critical test: requesting more than available must be
    rejected, and inventory must remain completely unchanged."""
    order_resp = client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": order_fixtures["retailer"].id,
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 15}],  # only 10 in stock
        },
    )
    order_id = order_resp.json()["id"]

    confirm_resp = client.patch(f"/api/orders/{order_id}/status", headers=admin_headers, json={"status": "CONFIRMED"})
    assert confirm_resp.status_code == 409
    assert "10 available" in confirm_resp.json()["detail"]
    assert "15 requested" in confirm_resp.json()["detail"]

    db_session.refresh(order_fixtures["inventory"])
    assert order_fixtures["inventory"].quantity == 10  # unchanged — the rollback worked


def test_invalid_status_transition_rejected(client, admin_headers, order_fixtures):
    """PENDING orders can't jump straight to DELIVERED."""
    order_resp = client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": order_fixtures["retailer"].id,
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 1}],
        },
    )
    order_id = order_resp.json()["id"]

    response = client.patch(f"/api/orders/{order_id}/status", headers=admin_headers, json={"status": "DELIVERED"})
    assert response.status_code == 409


def test_order_with_invalid_retailer_rejected(client, admin_headers, order_fixtures):
    response = client.post(
        "/api/orders", headers=admin_headers,
        json={
            "retailer_id": 999999,  # does not exist
            "distributor_id": order_fixtures["distributor"].id,
            "items": [{"product_id": order_fixtures["product"].id, "quantity": 1}],
        },
    )
    assert response.status_code == 422
