"""
Seed data generator.

WHY A PYTHON SCRIPT INSTEAD OF RAW seed_data.sql:
Generating 50 products, 10 distributors, 100 retailers, 200+ orders, and
500+ sales transactions by hand-written SQL INSERT statements would be
unmaintainable and error-prone (e.g. keeping foreign keys consistent
across hundreds of rows). A Python script using the SAME SQLAlchemy
models as the app itself guarantees every row satisfies the exact
constraints the app enforces, and lets us use realistic randomization
(via Faker) for retailer names/contacts while keeping the FMCG product
catalog deliberately realistic.

WHY THIS SCRIPT IS SAFE TO RE-RUN:
It checks for existing data first and refuses to double-seed — this
prevents duplicate rows if run twice by mistake (a real production
concern the spec explicitly asks the Excel import pipeline to handle
too — this script applies the same discipline).

Usage:
    python -m app.seed_data
"""
import random
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

from faker import Faker

from app.database import SessionLocal
from app.models import (
    Product, Distributor, Retailer, Inventory, Order, OrderItem,
    SalesTransaction, StockMovement, TroubleshootingIssue, User,
)
from app.models.enums import (
    DistributorStatus, RetailerStatus, OrderStatus, MovementType,
    IssueSeverity, IssueStatus, UserRole,
)
from app.utils.fmcg_reference_data import (
    PRODUCT_CATALOG, DISTRIBUTOR_CITIES, RETAILER_TYPES,
)
from app.utils.security import hash_password

fake = Faker("en_IN")
random.seed(42)  # deterministic seed data — same output every run, easier to debug/demo


def seed_users(db):
    users = [
        User(name="Admin User", email="admin@bizsync.com",
             password_hash=hash_password("admin123"), role=UserRole.ADMIN),
        User(name="Priya Sharma", email="priya.manager@bizsync.com",
             password_hash=hash_password("manager123"), role=UserRole.SALES_MANAGER),
        User(name="Rahul Verma", email="rahul.rep@bizsync.com",
             password_hash=hash_password("rep123"), role=UserRole.SALES_REP),
        User(name="Distributor Login", email="distributor@bizsync.com",
             password_hash=hash_password("dist123"), role=UserRole.DISTRIBUTOR),
        User(name="Ananya Iyer", email="ananya.analyst@bizsync.com",
             password_hash=hash_password("analyst123"), role=UserRole.ANALYST),
    ]
    db.add_all(users)
    db.flush()
    return users


def seed_products(db):
    products = []
    for i, (name, category, brand) in enumerate(PRODUCT_CATALOG, start=1):
        cost = round(random.uniform(15, 400), 2)
        margin = random.uniform(1.15, 1.45)  # 15-45% markup, realistic for FMCG
        products.append(Product(
            product_code=f"PRD{i:04d}",
            name=name,
            category=category,
            brand=brand,
            unit_price=Decimal(str(round(cost * margin, 2))),
            cost_price=Decimal(str(cost)),
            reorder_level=random.choice([15, 20, 25, 30, 50]),
            active=True,
        ))
    db.add_all(products)
    db.flush()
    return products


def seed_distributors(db):
    distributors = []
    for i, (city, state) in enumerate(DISTRIBUTOR_CITIES, start=1):
        distributors.append(Distributor(
            distributor_code=f"DIST{i:03d}",
            name=f"{city} FMCG Distribution Co.",
            contact_person=fake.name(),
            phone=fake.numerify("9#########"),
            email=f"contact@{city.lower()}distribution.example.com",
            city=city,
            state=state,
            status=DistributorStatus.ACTIVE,
        ))
    db.add_all(distributors)
    db.flush()
    return distributors


def seed_retailers(db, distributors, count=100):
    retailers = []
    for i in range(1, count + 1):
        distributor = random.choice(distributors)
        shop_type = random.choice(RETAILER_TYPES)
        retailers.append(Retailer(
            retailer_code=f"RTL{i:04d}",
            name=f"{fake.last_name()} {shop_type}",
            owner_name=fake.name(),
            phone=fake.numerify("9#########"),
            city=distributor.city,  # retailers cluster near their distributor's city — realistic
            state=distributor.state,
            distributor_id=distributor.id,
            status=RetailerStatus.ACTIVE,
        ))
    db.add_all(retailers)
    db.flush()
    return retailers


def seed_inventory(db, products, distributors):
    """One inventory row per (product, distributor) pair — matches the
    unique constraint on the Inventory model."""
    records = []
    for distributor in distributors:
        for product in products:
            qty = random.randint(0, 500)
            # Deliberately let some fall below reorder_level so LOW STOCK
            # / OUT OF STOCK logic (Phase 13) has real cases to detect.
            if random.random() < 0.1:
                qty = random.randint(0, product.reorder_level - 1)
            records.append(Inventory(
                product_id=product.id,
                distributor_id=distributor.id,
                quantity=qty,
                reserved_quantity=random.randint(0, min(20, qty)),
            ))
    db.add_all(records)
    db.flush()
    return records


def seed_orders_and_items(db, retailers, products, count=220):
    """Creates orders with 1-5 line items each, computing subtotals and
    totals the same way the real order-creation service will (Phase 8),
    so seed data matches production logic exactly."""
    orders = []
    all_items = []
    statuses = list(OrderStatus)
    # weight toward completed/delivered so analytics have real revenue,
    # but keep some pending/cancelled for workflow demo purposes
    status_weights = [0.05, 0.10, 0.10, 0.15, 0.50, 0.10]

    start_date = date.today() - timedelta(days=180)

    for i in range(1, count + 1):
        retailer = random.choice(retailers)
        order_date = start_date + timedelta(days=random.randint(0, 180))
        status = random.choices(statuses, weights=status_weights, k=1)[0]

        order = Order(
            order_number=f"ORD{i:05d}",
            retailer_id=retailer.id,
            distributor_id=retailer.distributor_id,
            order_date=order_date,
            status=status,
            total_amount=Decimal("0"),  # filled in after items are computed
        )
        db.add(order)
        db.flush()  # need order.id for items

        num_items = random.randint(1, 5)
        chosen_products = random.sample(products, num_items)
        total = Decimal("0")
        for product in chosen_products:
            qty = random.randint(5, 100)
            unit_price = product.unit_price
            subtotal = (unit_price * qty).quantize(Decimal("0.01"))
            total += subtotal
            all_items.append(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal,
            ))
        order.total_amount = total
        orders.append(order)

    db.add_all(all_items)
    db.flush()
    return orders, all_items


def seed_sales_transactions(db, orders, count=520):
    """Sales transactions represent COMPLETED sales — derived mainly
    from DELIVERED orders (realistic: a sale is only 'final' once
    delivered), with some extra standalone transactions to comfortably
    exceed the 500+ requirement."""
    transactions = []
    delivered_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]

    # One transaction per line item of every delivered order
    for order in delivered_orders:
        for item in order.items:
            revenue = item.subtotal
            cost = (item.product.cost_price * item.quantity).quantize(Decimal("0.01"))
            transactions.append(SalesTransaction(
                transaction_date=order.order_date,
                retailer_id=order.retailer_id,
                distributor_id=order.distributor_id,
                product_id=item.product_id,
                quantity=item.quantity,
                revenue=revenue,
                cost=cost,
                profit=(revenue - cost).quantize(Decimal("0.01")),
            ))

    # Top up with extra standalone transactions (simulating direct/cash
    # sales not tied to a formal order) so we comfortably clear 500+
    while len(transactions) < count:
        order = random.choice(orders)
        item = random.choice(order.items) if order.items else None
        if not item:
            continue
        qty = random.randint(1, 30)
        revenue = (item.unit_price * qty).quantize(Decimal("0.01"))
        cost = (item.product.cost_price * qty).quantize(Decimal("0.01"))
        transactions.append(SalesTransaction(
            transaction_date=order.order_date,
            retailer_id=order.retailer_id,
            distributor_id=order.distributor_id,
            product_id=item.product_id,
            quantity=qty,
            revenue=revenue,
            cost=cost,
            profit=(revenue - cost).quantize(Decimal("0.01")),
        ))

    db.add_all(transactions)
    db.flush()
    return transactions


def seed_stock_movements(db, inventory_records, orders):
    """Builds a plausible movement history: an initial PURCHASE per
    inventory record (explaining how stock got there), plus a SALE
    movement for every delivered order's line items (explaining stock
    leaving) — so the movement history feature (Phase 13) has a
    coherent story, not just random rows."""
    movements = []

    for inv in inventory_records:
        if inv.quantity > 0:
            movements.append(StockMovement(
                product_id=inv.product_id,
                distributor_id=inv.distributor_id,
                movement_type=MovementType.PURCHASE,
                quantity=inv.quantity + random.randint(0, 100),  # bought slightly more than current stock
                reference_id=None,
            ))

    for order in orders:
        if order.status in (OrderStatus.DELIVERED, OrderStatus.SHIPPED):
            for item in order.items:
                movements.append(StockMovement(
                    product_id=item.product_id,
                    distributor_id=order.distributor_id,
                    movement_type=MovementType.SALE,
                    quantity=-item.quantity,
                    reference_id=order.id,
                ))

    db.add_all(movements)
    db.flush()
    return movements


def seed_troubleshooting_issues(db, users):
    admin = next(u for u in users if u.role == UserRole.ADMIN)
    analyst = next(u for u in users if u.role == UserRole.ANALYST)

    issues = [
        TroubleshootingIssue(
            title="Inventory mismatch after Excel import",
            description="Distributor-reported stock counts did not match system inventory after a bulk Excel upload of purchase records.",
            severity=IssueSeverity.HIGH,
            module="Excel Import",
            status=IssueStatus.RESOLVED,
            reported_by=analyst.id,
            assigned_to=admin.id,
            resolved_at=datetime.now(timezone.utc) - timedelta(days=10),
            root_cause="Duplicate transaction IDs existed in the uploaded Excel file, causing the same purchase to be applied to inventory twice.",
            resolution="Added duplicate-detection validation (by transaction ID) to the Excel import pipeline before any database insert occurs.",
        ),
        TroubleshootingIssue(
            title="Dashboard sales-trend chart showing incorrect totals",
            description="Sales trend chart on the dashboard displayed lower totals than the sum of visible sales transactions for the same period.",
            severity=IssueSeverity.MEDIUM,
            module="Analytics Dashboard",
            status=IssueStatus.RESOLVED,
            reported_by=analyst.id,
            assigned_to=admin.id,
            resolved_at=datetime.now(timezone.utc) - timedelta(days=25),
            root_cause="SQL aggregation query grouped by transaction_date without accounting for timezone offset, dropping late-night transactions into the wrong day bucket.",
            resolution="Standardized all date grouping to use the database's stored date value directly rather than converting through application-server timezone.",
        ),
        TroubleshootingIssue(
            title="Order confirmation occasionally allowed overselling",
            description="Two orders confirmed in quick succession for the same product/distributor briefly oversold available inventory.",
            severity=IssueSeverity.CRITICAL,
            module="Orders",
            status=IssueStatus.RESOLVED,
            reported_by=admin.id,
            assigned_to=admin.id,
            resolved_at=datetime.now(timezone.utc) - timedelta(days=45),
            root_cause="Inventory availability was checked and updated in two separate, non-atomic database calls, creating a race condition under concurrent requests.",
            resolution="Wrapped the check-and-update in a single database transaction using row-level locking (SELECT ... FOR UPDATE) so concurrent confirmations can't both pass the same availability check.",
        ),
        TroubleshootingIssue(
            title="Low-stock alerts not appearing for some products",
            description="A handful of products below their reorder level were not appearing in the dashboard's low-stock list.",
            severity=IssueSeverity.LOW,
            module="Inventory",
            status=IssueStatus.OPEN,
            reported_by=analyst.id,
            assigned_to=None,
            root_cause=None,
            resolution=None,
        ),
    ]
    db.add_all(issues)
    db.flush()
    return issues


def run():
    db = SessionLocal()
    try:
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print(f"Database already has {existing_products} products — skipping seed to avoid duplicates.")
            print("If you want to reseed from scratch, drop and recreate the tables first.")
            return

        print("Seeding users...")
        users = seed_users(db)

        print("Seeding products...")
        products = seed_products(db)

        print("Seeding distributors...")
        distributors = seed_distributors(db)

        print("Seeding retailers...")
        retailers = seed_retailers(db, distributors, count=100)

        print("Seeding inventory...")
        inventory_records = seed_inventory(db, products, distributors)

        print("Seeding orders and order items...")
        orders, items = seed_orders_and_items(db, retailers, products, count=220)

        print("Seeding sales transactions...")
        transactions = seed_sales_transactions(db, orders, count=520)

        print("Seeding stock movements...")
        movements = seed_stock_movements(db, inventory_records, orders)

        print("Seeding troubleshooting issues...")
        issues = seed_troubleshooting_issues(db, users)

        db.commit()

        print("\nSeed complete:")
        print(f"  users:                  {len(users)}")
        print(f"  products:               {len(products)}")
        print(f"  distributors:           {len(distributors)}")
        print(f"  retailers:              {len(retailers)}")
        print(f"  inventory records:      {len(inventory_records)}")
        print(f"  orders:                 {len(orders)}")
        print(f"  order items:            {len(items)}")
        print(f"  sales transactions:     {len(transactions)}")
        print(f"  stock movements:        {len(movements)}")
        print(f"  troubleshooting issues: {len(issues)}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
