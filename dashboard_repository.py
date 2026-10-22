"""
Dashboard repository.

WHY EVERY FUNCTION HERE USES SQL AGGREGATION (SUM/COUNT/GROUP BY)
INSTEAD OF FETCHING ROWS AND SUMMING IN PYTHON: with 500+ sales
transactions and growing, pulling every row into Python just to add
them up wastes both network bandwidth (transferring rows) and memory,
and doesn't scale — the same query pattern would still work correctly
at 5 million rows, just slower, whereas a Python-side loop would
eventually run out of memory. This directly answers the spec's
question: "How are dashboard analytics calculated?" -> "Via SQL
aggregate functions executed by Postgres, not by loading raw
transactions into the application."
"""
from datetime import date
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.distributor import Distributor
from app.models.retailer import Retailer
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.sales_transaction import SalesTransaction
from app.models.enums import OrderStatus


def get_summary(db: Session) -> dict:
    total_revenue = db.execute(select(func.coalesce(func.sum(SalesTransaction.revenue), 0))).scalar_one()
    total_orders = db.execute(select(func.count()).select_from(Order)).scalar_one()
    total_products = db.execute(select(func.count()).select_from(Product).where(Product.active.is_(True))).scalar_one()
    total_retailers = db.execute(select(func.count()).select_from(Retailer)).scalar_one()
    total_distributors = db.execute(select(func.count()).select_from(Distributor)).scalar_one()
    total_inventory_units = db.execute(select(func.coalesce(func.sum(Inventory.quantity), 0))).scalar_one()

    # LOW STOCK rule, applied in SQL via a JOIN — same rule used by the
    # inventory router's low_stock_only filter (Phase 4), kept
    # consistent so the dashboard number always matches what a user
    # sees when they click through to the Inventory page.
    low_stock_products = db.execute(
        select(func.count()).select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .where((Inventory.quantity - Inventory.reserved_quantity) <= Product.reorder_level)
    ).scalar_one()

    pending_orders = db.execute(
        select(func.count()).select_from(Order).where(Order.status == OrderStatus.PENDING)
    ).scalar_one()

    return dict(
        total_revenue=total_revenue, total_orders=total_orders, total_products=total_products,
        total_retailers=total_retailers, total_distributors=total_distributors,
        total_inventory_units=total_inventory_units, low_stock_products=low_stock_products,
        pending_orders=pending_orders,
    )


def get_sales_trend(db: Session, date_from: date, date_to: date, granularity: str = "daily") -> list[dict]:
    """granularity: 'daily' groups by exact date; 'monthly' groups by
    year-month. Both use Postgres's own date_trunc/to_char rather than
    fetching rows and bucketing them in Python."""
    if granularity == "monthly":
        period_expr = func.to_char(SalesTransaction.transaction_date, "YYYY-MM")
    else:
        period_expr = func.to_char(SalesTransaction.transaction_date, "YYYY-MM-DD")

    rows = db.execute(
        select(
            period_expr.label("period"),
            func.sum(SalesTransaction.revenue).label("revenue"),
            func.count(func.distinct(SalesTransaction.id)).label("order_count"),
        )
        .where(SalesTransaction.transaction_date.between(date_from, date_to))
        .group_by(period_expr)
        .order_by(period_expr)
    ).all()
    return [dict(period=r.period, revenue=r.revenue, order_count=r.order_count) for r in rows]


def get_top_products(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.category.label("category"),
            func.sum(SalesTransaction.quantity).label("total_quantity"),
            func.sum(SalesTransaction.revenue).label("total_revenue"),
        )
        .join(SalesTransaction, SalesTransaction.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.category)
        .order_by(func.sum(SalesTransaction.revenue).desc())
        .limit(limit)
    ).all()
    return [dict(r._mapping) for r in rows]


def get_top_retailers(db: Session, limit: int = 10) -> list[dict]:
    """
    WHY ORDER COUNT AND REVENUE ARE TWO SEPARATE QUERIES, NOT ONE JOIN:
    a naive query joining Retailer -> Order -> SalesTransaction in a
    single statement would fan out — if a retailer has 5 orders and 20
    sales transactions, the join produces up to 100 combined rows,
    which would inflate SUM(revenue) far beyond the real total. Two
    independent aggregations, merged by retailer_id in Python, avoids
    this entirely while still doing all the actual summing in SQL.
    """
    revenue_rows = db.execute(
        select(
            SalesTransaction.retailer_id,
            func.sum(SalesTransaction.revenue).label("total_revenue"),
        ).group_by(SalesTransaction.retailer_id)
    ).all()
    revenue_by_retailer = {r.retailer_id: r.total_revenue for r in revenue_rows}

    order_count_rows = db.execute(
        select(Order.retailer_id, func.count()).group_by(Order.retailer_id)
    ).all()
    orders_by_retailer = dict(order_count_rows)

    retailers = db.execute(select(Retailer.id, Retailer.name)).all()

    combined = [
        dict(
            retailer_id=r.id,
            retailer_name=r.name,
            total_orders=orders_by_retailer.get(r.id, 0),
            total_revenue=revenue_by_retailer.get(r.id, 0) or 0,
        )
        for r in retailers
    ]
    combined.sort(key=lambda x: x["total_revenue"], reverse=True)
    return combined[:limit]


def get_category_performance(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Product.category.label("category"),
            func.sum(SalesTransaction.revenue).label("total_revenue"),
            func.sum(SalesTransaction.quantity).label("total_quantity"),
        )
        .join(SalesTransaction, SalesTransaction.product_id == Product.id)
        .group_by(Product.category)
        .order_by(func.sum(SalesTransaction.revenue).desc())
    ).all()
    return [dict(r._mapping) for r in rows]


def get_distributor_performance(db: Session) -> list[dict]:
    """See get_top_retailers docstring for why revenue, order count,
    retailer count, and inventory value are each computed as
    INDEPENDENT aggregations rather than one multi-table join — the
    same fan-out risk applies here with even more joined tables."""
    revenue_by_dist = dict(db.execute(
        select(SalesTransaction.distributor_id, func.sum(SalesTransaction.revenue))
        .group_by(SalesTransaction.distributor_id)
    ).all())
    orders_by_dist = dict(db.execute(
        select(Order.distributor_id, func.count()).group_by(Order.distributor_id)
    ).all())
    retailer_counts = dict(db.execute(
        select(Retailer.distributor_id, func.count()).group_by(Retailer.distributor_id)
    ).all())
    inventory_values = dict(db.execute(
        select(Inventory.distributor_id, func.sum(Inventory.quantity * Product.unit_price))
        .join(Product, Product.id == Inventory.product_id)
        .group_by(Inventory.distributor_id)
    ).all())

    distributors = db.execute(select(Distributor.id, Distributor.name)).all()

    combined = [
        dict(
            distributor_id=d.id,
            distributor_name=d.name,
            total_revenue=revenue_by_dist.get(d.id, 0) or 0,
            total_orders=orders_by_dist.get(d.id, 0),
            retailer_count=retailer_counts.get(d.id, 0),
            inventory_value=inventory_values.get(d.id, 0) or 0,
        )
        for d in distributors
    ]
    combined.sort(key=lambda x: x["total_revenue"], reverse=True)
    return combined
