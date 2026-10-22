import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.distributor import DistributorCreate, DistributorUpdate, DistributorResponse
from app.schemas.common import PaginatedResponse
from app.schemas.auth import CurrentUser
from app.services import distributor_service
from app.utils.deps import get_current_user, require_role
from app.models.enums import UserRole

router = APIRouter(prefix="/distributors", tags=["Distributors"])


@router.get("", response_model=PaginatedResponse[DistributorResponse])
def list_distributors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = distributor_service.list_distributors(db, page, page_size, search)
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=DistributorResponse, status_code=status.HTTP_201_CREATED)
def create_distributor(
    payload: DistributorCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
):
    try:
        distributor = distributor_service.create_distributor(db, payload.model_dump())
        db.commit()
        db.refresh(distributor)
        return distributor
    except distributor_service.DuplicateDistributorCodeError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Distributor code '{e}' already exists")


@router.get("/{distributor_id}", response_model=DistributorResponse)
def get_distributor(
    distributor_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        return distributor_service.get_distributor(db, distributor_id)
    except distributor_service.DistributorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")


@router.put("/{distributor_id}", response_model=DistributorResponse)
def update_distributor(
    distributor_id: int,
    payload: DistributorUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
):
    try:
        changes = payload.model_dump(exclude_unset=True)
        distributor = distributor_service.update_distributor(db, distributor_id, changes)
        db.commit()
        db.refresh(distributor)
        return distributor
    except distributor_service.DistributorNotFoundError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")


@router.get("/{distributor_id}/retailer-count")
def get_distributor_retailer_count(
    distributor_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        distributor_service.get_distributor(db, distributor_id)  # 404 if missing
        count = distributor_service.get_retailer_count(db, distributor_id)
        return {"distributor_id": distributor_id, "retailer_count": count}
    except distributor_service.DistributorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")
