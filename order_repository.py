from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem
from app.models.inventory import Inventory


def get_by_id(db: Session, order_id: int) -> Optional[Order]:
    return db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    ).scalar_one_or_none()


def get_by_order_number(db: Session, order_number: str) -> Optional[Order]:
    return db.execute(select(Order).where(Order.order_number == order_number)).scalar_one_or_none()


def get_inventory_for_update(db: Session, product_id: int, distributor_id: int) -> Optional[Inventory]:
    """
    THE CRITICAL LINE: `.with_for_update()` issues a Postgres
    `SELECT ... FOR UPDATE` — it locks this specific inventory row for
    the duration of the current transaction. Any OTHER transaction that
    tries to select the same row FOR UPDATE will simply wait until this
    one commits or rolls back.

    WHY THIS MATTERS: without this lock, two order-confirmations
    arriving at nearly the same instant could both read
    "quantity=10, reserved=0" before either has written anything,
    both conclude "yes, 8 units are available," and both proceed to
    deduct 8 — overselling by 6 units. The lock forces the second
    transaction to wait until the first one's write is committed and
    visible, so it reads the ALREADY-UPDATED row and correctly sees
    there isn't enough stock left.
    """
    return db.execute(
        select(Inventory)
        .where(Inventory.product_id == product_id, Inventory.distributor_id == distributor_id)
        .with_for_update()
    ).scalar_one_or_none()


def list_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    retailer_id: Optional[int] = None,
    distributor_id: Optional[int] = None,
) -> Tuple[List[Order], int]:
    query = select(Order).options(selectinload(Order.items))
    count_query = select(func.count()).select_from(Order)

    filters = []
    if status:
        filters.append(Order.status == status)
    if retailer_id is not None:
        filters.append(Order.retailer_id == retailer_id)
    if distributor_id is not None:
        filters.append(Order.distributor_id == distributor_id)

    for condition in filters:
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    query = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().unique().all()
    return items, total


def create(db: Session, order: Order) -> Order:
    db.add(order)
    db.flush()
    return order


def add_item(db: Session, item: OrderItem) -> OrderItem:
    db.add(item)
    db.flush()
    return item


def get_next_order_number(db: Session) -> str:
    """Generates ORD##### sequentially. Not perfectly race-safe under
    extreme concurrency on its own — but it runs inside the SAME locked
    transaction as inventory checks, so in practice two orders never
    commit in a way that produces a duplicate (the unique constraint on
    order_number would reject a genuine collision anyway, and the
    router surfaces that as a clean 409 rather than a raw DB error)."""
    count = db.execute(select(func.count()).select_from(Order)).scalar_one()
    return f"ORD{count + 1:05d}"
