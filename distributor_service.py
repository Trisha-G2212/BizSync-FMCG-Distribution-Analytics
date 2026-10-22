from typing import Optional
from sqlalchemy.orm import Session

from app.models.distributor import Distributor
from app.repositories import distributor_repository


class DuplicateDistributorCodeError(Exception):
    pass


class DistributorNotFoundError(Exception):
    pass


def create_distributor(db: Session, data: dict) -> Distributor:
    if distributor_repository.get_by_code(db, data["distributor_code"]):
        raise DuplicateDistributorCodeError(data["distributor_code"])
    distributor = Distributor(**data)
    return distributor_repository.create(db, distributor)


def get_distributor(db: Session, distributor_id: int) -> Distributor:
    distributor = distributor_repository.get_by_id(db, distributor_id)
    if not distributor:
        raise DistributorNotFoundError(distributor_id)
    return distributor


def update_distributor(db: Session, distributor_id: int, changes: dict) -> Distributor:
    distributor = get_distributor(db, distributor_id)
    return distributor_repository.update(db, distributor, changes)


def list_distributors(db: Session, page: int, page_size: int, search: Optional[str]):
    return distributor_repository.list_distributors(db, page, page_size, search)


def get_retailer_count(db: Session, distributor_id: int) -> int:
    return distributor_repository.count_retailers(db, distributor_id)
