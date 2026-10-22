from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.inventory import Inventory


def get_by_product_and_distributor(db: Session, product_id: int, distributor_id: int) -> Optional[Inventory]:
    return db.execute(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.distributor_id == distributor_id,
        )
    ).scalar_one_or_none()


def list_inventory(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    distributor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    low_stock_only: bool = False,
) -> Tuple[List[Inventory], int]:
    from app.models.product import Product  # local import avoids circular import at module load

    query = select(Inventory)
    count_query = select(func.count()).select_from(Inventory)

    if distributor_id is not None:
        query = query.where(Inventory.distributor_id == distributor_id)
        count_query = count_query.where(Inventory.distributor_id == distributor_id)

    if product_id is not None:
        query = query.where(Inventory.product_id == product_id)
        count_query = count_query.where(Inventory.product_id == product_id)

    if low_stock_only:
        # LOW STOCK business rule: available quantity <= the product's reorder_level
        query = query.join(Product, Product.id == Inventory.product_id).where(
            (Inventory.quantity - Inventory.reserved_quantity) <= Product.reorder_level
        )
        count_query = count_query.join(Product, Product.id == Inventory.product_id).where(
            (Inventory.quantity - Inventory.reserved_quantity) <= Product.reorder_level
        )

    total = db.execute(count_query).scalar_one()
    query = query.order_by(Inventory.id).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    return items, total
