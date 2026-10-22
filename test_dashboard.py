"""
Dashboard aggregation tests.

WHY THESE TESTS SEED EXACT, KNOWN NUMBERS: the whole point of testing
aggregation logic is to know precisely what the correct answer should
be. Seeding two sales transactions of known amounts and asserting the
summary returns EXACTLY their sum (not just "a positive number") is
what actually catches bugs like the fan-out join issue found during
Phase 10 development — a vague assertion would have let that bug pass.
"""
from datetime import date
from app.models.distributor import Distributor
from app.models.retailer import Retailer
from app.models.product import Product
from app.models.sales_transaction import SalesTransaction
from app.models.enums import DistributorStatus, RetailerStatus


def seed_known_sales(db_session):
    distributor = Distributor(
        distributor_code="DASHDIST", name="Dashboard Test Distributor", contact_person="T",
        phone="1234567890", email="t@t.test", city="City", state="State", status=DistributorStatus.ACTIVE,
    )
    db_session.add(distributor)
    db_session.flush()

    retailer = Retailer(
        retailer_code="DASHRET", name="Dashboard Test Retailer", owner_name="T",
        phone="1234567890", city="City", state="State",
        distributor_id=distributor.id, status=RetailerStatus.ACTIVE,
    )
    db_session.add(retailer)

    product = Product(
        product_code="DASHPROD", name="Dashboard Test Product", category="Snacks",
        brand="B", unit_price=100.0, cost_price=60.0, reorder_level=10,
    )
    db_session.add(product)
    db_session.flush()

    # Two known transactions: 1000 + 500 = 1500 total revenue
    db_session.add(SalesTransaction(
        transaction_date=date.today(), retailer_id=retailer.id, distributor_id=distributor.id,
        product_id=product.id, quantity=10, revenue=1000, cost=600, profit=400,
    ))
    db_session.add(SalesTransaction(
        transaction_date=date.today(), retailer_id=retailer.id, distributor_id=distributor.id,
        product_id=product.id, quantity=5, revenue=500, cost=300, profit=200,
    ))
    db_session.commit()
    return distributor, retailer, product


def test_dashboard_summary_revenue_matches_exact_sum(client, admin_headers, db_session):
    seed_known_sales(db_session)
    response = client.get("/api/dashboard/summary", headers=admin_headers)
    assert response.status_code == 200
    assert float(response.json()["total_revenue"]) == 1500.0


def test_distributor_performance_does_not_inflate_via_fan_out(client, admin_headers, db_session):
    """
    Regression test for the exact bug found during Phase 10
    development: joining Orders and SalesTransactions in one query
    multiplies rows and inflates the revenue sum. This test seeds a
    known revenue total and asserts it comes back EXACT, not multiplied.
    """
    distributor, retailer, product = seed_known_sales(db_session)

    response = client.get("/api/dashboard/distributor-performance", headers=admin_headers)
    assert response.status_code == 200
    results = {r["distributor_id"]: r for r in response.json()}
    assert distributor.id in results
    assert float(results[distributor.id]["total_revenue"]) == 1500.0  # NOT 1500 * order_count


def test_category_performance_matches_known_total(client, admin_headers, db_session):
    seed_known_sales(db_session)
    response = client.get("/api/dashboard/category-performance", headers=admin_headers)
    assert response.status_code == 200
    snacks = next(r for r in response.json() if r["category"] == "Snacks")
    assert float(snacks["total_revenue"]) == 1500.0


def test_top_products_ranks_by_revenue(client, admin_headers, db_session):
    distributor, retailer, product = seed_known_sales(db_session)
    response = client.get("/api/dashboard/top-products?limit=5", headers=admin_headers)
    assert response.status_code == 200
    top = response.json()[0]
    assert top["product_id"] == product.id
    assert float(top["total_revenue"]) == 1500.0
