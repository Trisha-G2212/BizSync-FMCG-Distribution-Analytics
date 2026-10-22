from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories import dashboard_repository


def get_summary(db: Session):
    return dashboard_repository.get_summary(db)


def get_sales_trend(db: Session, date_from: Optional[date], date_to: Optional[date], granularity: str):
    # Default window: last 30 days — a sensible default for a "trend"
    # view rather than forcing the caller to always specify a range.
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=30))
    return dashboard_repository.get_sales_trend(db, date_from, date_to, granularity)


def get_top_products(db: Session, limit: int):
    return dashboard_repository.get_top_products(db, limit)


def get_top_retailers(db: Session, limit: int):
    return dashboard_repository.get_top_retailers(db, limit)


def get_category_performance(db: Session):
    return dashboard_repository.get_category_performance(db)


def get_distributor_performance(db: Session):
    return dashboard_repository.get_distributor_performance(db)
