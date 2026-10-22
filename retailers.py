import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.retailer import RetailerCreate, RetailerUpdate, RetailerResponse
from app.schemas.common import PaginatedResponse
from app.schemas.auth import CurrentUser
from app.services import retailer_service
from app.utils.deps import get_current_user, require_role
from app.models.enums import UserRole

router = APIRouter(prefix="/retailers", tags=["Retailers"])


@router.get("", response_model=PaginatedResponse[RetailerResponse])
def list_retailers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    distributor_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = retailer_service.list_retailers(db, page, page_size, search, distributor_id, city)
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=RetailerResponse, status_code=status.HTTP_201_CREATED)
def create_retailer(
    payload: RetailerCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER)),
):
    try:
        retailer = retailer_service.create_retailer(db, payload.model_dump())
        db.commit()
        db.refresh(retailer)
        return retailer
    except retailer_service.DuplicateRetailerCodeError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Retailer code '{e}' already exists")
    except retailer_service.InvalidDistributorError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Distributor {e} does not exist")


@router.get("/{retailer_id}", response_model=RetailerResponse)
def get_retailer(
    retailer_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        return retailer_service.get_retailer(db, retailer_id)
    except retailer_service.RetailerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retailer not found")


@router.put("/{retailer_id}", response_model=RetailerResponse)
def update_retailer(
    retailer_id: int,
    payload: RetailerUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER)),
):
    try:
        changes = payload.model_dump(exclude_unset=True)
        retailer = retailer_service.update_retailer(db, retailer_id, changes)
        db.commit()
        db.refresh(retailer)
        return retailer
    except retailer_service.RetailerNotFoundError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retailer not found")
    except retailer_service.InvalidDistributorError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Distributor {e} does not exist")
