"""
Product repository.

WHY THIS LAYER EXISTS SEPARATELY FROM THE ROUTER:
Repositories know ONLY how to talk to the database — they take/return
SQLAlchemy model instances or primitives, never HTTP concepts (no
status codes, no Pydantic schemas). This means the exact same query
logic here could be reused by a future CLI tool, a background job, or
a test — anything that needs "the product with this code," not just
the HTTP API. It also makes services (Phase 4 business logic) testable
without needing a real HTTP request.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.product import Product


def get_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.get(Product, product_id)


def get_by_code(db: Session, product_code: str) -> Optional[Product]:
    return db.execute(
        select(Product).where(Product.product_code == product_code)
    ).scalar_one_or_none()


def list_products(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    active: Optional[bool] = None,
) -> Tuple[List[Product], int]:
    """Returns (items, total_count). Filtering and pagination happen in
    SQL, not Python — we never pull the whole table into memory just to
    slice it (see spec section 28: performance)."""
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if search:
        like_pattern = f"%{search}%"
        condition = or_(Product.name.ilike(like_pattern), Product.product_code.ilike(like_pattern))
        query = query.where(condition)
        count_query = count_query.where(condition)

    if category:
        query = query.where(Product.category == category)
        count_query = count_query.where(Product.category == category)

    if active is not None:
        query = query.where(Product.active == active)
        count_query = count_query.where(Product.active == active)

    total = db.execute(count_query).scalar_one()

    query = query.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()

    return items, total


def create(db: Session, product: Product) -> Product:
    db.add(product)
    db.flush()
    return product


def update(db: Session, product: Product, changes: dict) -> Product:
    for field, value in changes.items():
        setattr(product, field, value)
    db.flush()
    return product


def deactivate(db: Session, product: Product) -> Product:
    product.active = False
    db.flush()
    return product


def delete(db: Session, product: Product) -> None:
    db.delete(product)
    db.flush()
