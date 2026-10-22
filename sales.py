import math
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sales_transaction import SalesTransactionResponse
from app.schemas.common import PaginatedResponse
from app.schemas.auth import CurrentUser
from app.repositories import sales_repository
from app.utils.deps import get_current_user

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("", response_model=PaginatedResponse[SalesTransactionResponse])
def list_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    distributor_id: Optional[int] = Query(None),
    retailer_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = sales_repository.list_sales(
        db, page, page_size, distributor_id, retailer_id, product_id, date_from, date_to
    )
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )
