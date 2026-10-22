from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.distributor import Distributor
from app.models.retailer import Retailer


def get_by_id(db: Session, distributor_id: int) -> Optional[Distributor]:
    return db.get(Distributor, distributor_id)


def get_by_code(db: Session, distributor_code: str) -> Optional[Distributor]:
    return db.execute(
        select(Distributor).where(Distributor.distributor_code == distributor_code)
    ).scalar_one_or_none()


def list_distributors(
    db: Session, page: int = 1, page_size: int = 20, search: Optional[str] = None
) -> Tuple[List[Distributor], int]:
    query = select(Distributor)
    count_query = select(func.count()).select_from(Distributor)

    if search:
        like_pattern = f"%{search}%"
        condition = or_(Distributor.name.ilike(like_pattern), Distributor.distributor_code.ilike(like_pattern))
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    query = query.order_by(Distributor.id).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    return items, total


def create(db: Session, distributor: Distributor) -> Distributor:
    db.add(distributor)
    db.flush()
    return distributor


def update(db: Session, distributor: Distributor, changes: dict) -> Distributor:
    for field, value in changes.items():
        setattr(distributor, field, value)
    db.flush()
    return distributor


def count_retailers(db: Session, distributor_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(Retailer).where(Retailer.distributor_id == distributor_id)
    ).scalar_one()
