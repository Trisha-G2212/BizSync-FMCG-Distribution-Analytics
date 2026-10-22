from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.sales_transaction import SalesTransaction


def list_sales(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    distributor_id: Optional[int] = None,
    retailer_id: Optional[int] = None,
    product_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Tuple[List[SalesTransaction], int]:
    query = select(SalesTransaction)
    count_query = select(func.count()).select_from(SalesTransaction)

    filters = []
    if distributor_id is not None:
        filters.append(SalesTransaction.distributor_id == distributor_id)
    if retailer_id is not None:
        filters.append(SalesTransaction.retailer_id == retailer_id)
    if product_id is not None:
        filters.append(SalesTransaction.product_id == product_id)
    if date_from is not None:
        filters.append(SalesTransaction.transaction_date >= date_from)
    if date_to is not None:
        filters.append(SalesTransaction.transaction_date <= date_to)

    for condition in filters:
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    query = query.order_by(SalesTransaction.transaction_date.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    return items, total
