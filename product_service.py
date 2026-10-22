"""
Product service — business logic layer.

WHY THIS LAYER EXISTS: the router shouldn't know HOW a duplicate
product_code is detected, and the repository shouldn't know that a
duplicate is an HTTP 409 (that's an HTTP concept, not a database one).
The service is the middle layer that turns "a business rule was
violated" into a well-defined error the router layer can translate to
the right status code. This is what makes the answer to "how is
business logic isolated?" concrete rather than theoretical.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories import product_repository


class DuplicateProductCodeError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


def create_product(db: Session, data: dict) -> Product:
    existing = product_repository.get_by_code(db, data["product_code"])
    if existing:
        raise DuplicateProductCodeError(data["product_code"])
    product = Product(**data)
    return product_repository.create(db, product)


def get_product(db: Session, product_id: int) -> Product:
    product = product_repository.get_by_id(db, product_id)
    if not product:
        raise ProductNotFoundError(product_id)
    return product


def update_product(db: Session, product_id: int, changes: dict) -> Product:
    product = get_product(db, product_id)
    return product_repository.update(db, product, changes)


def deactivate_product(db: Session, product_id: int) -> Product:
    """Spec explicitly asks for deactivate rather than hard-delete as
    the normal path (products referenced by historical orders/sales
    transactions should never disappear — that would break referential
    history). Hard delete is offered separately for genuine mistakes."""
    product = get_product(db, product_id)
    return product_repository.deactivate(db, product)


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    product_repository.delete(db, product)


def list_products(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str],
    category: Optional[str],
    active: Optional[bool],
):
    return product_repository.list_products(db, page, page_size, search, category, active)
