from typing import Optional
from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.repositories import retailer_repository, distributor_repository


class DuplicateRetailerCodeError(Exception):
    pass


class RetailerNotFoundError(Exception):
    pass


class InvalidDistributorError(Exception):
    """Raised when a retailer references a distributor_id that doesn't
    exist — an explicit foreign-key validation at the service layer,
    so the error message can be specific ('distributor 47 does not
    exist') rather than a raw, unreadable Postgres FK-violation error."""
    pass


def create_retailer(db: Session, data: dict) -> Retailer:
    if retailer_repository.get_by_code(db, data["retailer_code"]):
        raise DuplicateRetailerCodeError(data["retailer_code"])
    if not distributor_repository.get_by_id(db, data["distributor_id"]):
        raise InvalidDistributorError(data["distributor_id"])
    retailer = Retailer(**data)
    return retailer_repository.create(db, retailer)


def get_retailer(db: Session, retailer_id: int) -> Retailer:
    retailer = retailer_repository.get_by_id(db, retailer_id)
    if not retailer:
        raise RetailerNotFoundError(retailer_id)
    return retailer


def update_retailer(db: Session, retailer_id: int, changes: dict) -> Retailer:
    retailer = get_retailer(db, retailer_id)
    if "distributor_id" in changes and not distributor_repository.get_by_id(db, changes["distributor_id"]):
        raise InvalidDistributorError(changes["distributor_id"])
    return retailer_repository.update(db, retailer, changes)


def list_retailers(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str],
    distributor_id: Optional[int],
    city: Optional[str],
):
    return retailer_repository.list_retailers(db, page, page_size, search, distributor_id, city)
