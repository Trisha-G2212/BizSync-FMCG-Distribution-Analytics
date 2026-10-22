from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.retailer import Retailer


def get_by_id(db: Session, retailer_id: int) -> Optional[Retailer]:
    return db.get(Retailer, retailer_id)


def get_by_code(db: Session, retailer_code: str) -> Optional[Retailer]:
    return db.execute(
        select(Retailer).where(Retailer.retailer_code == retailer_code)
    ).scalar_one_or_none()


def list_retailers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    distributor_id: Optional[int] = None,
    city: Optional[str] = None,
) -> Tuple[List[Retailer], int]:
    query = select(Retailer)
    count_query = select(func.count()).select_from(Retailer)

    if search:
        like_pattern = f"%{search}%"
        condition = or_(Retailer.name.ilike(like_pattern), Retailer.retailer_code.ilike(like_pattern))
        query = query.where(condition)
        count_query = count_query.where(condition)

    if distributor_id is not None:
        query = query.where(Retailer.distributor_id == distributor_id)
        count_query = count_query.where(Retailer.distributor_id == distributor_id)

    if city:
        query = query.where(Retailer.city == city)
        count_query = count_query.where(Retailer.city == city)

    total = db.execute(count_query).scalar_one()
    query = query.order_by(Retailer.id).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    return items, total


def create(db: Session, retailer: Retailer) -> Retailer:
    db.add(retailer)
    db.flush()
    return retailer


def update(db: Session, retailer: Retailer, changes: dict) -> Retailer:
    for field, value in changes.items():
        setattr(retailer, field, value)
    db.flush()
    return retailer
