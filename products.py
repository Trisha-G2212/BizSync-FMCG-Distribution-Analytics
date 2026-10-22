"""
Products router.

WHY EXCEPTIONS ARE CAUGHT HERE, NOT IN THE SERVICE: only the HTTP layer
knows about status codes. The service raises plain Python exceptions
(DuplicateProductCodeError, ProductNotFoundError) that mean nothing
outside HTTP — this router is the one place that decides
DuplicateProductCodeError -> 409, ProductNotFoundError -> 404. If we
ever added a CLI import tool reusing product_service, it wouldn't need
to know or care about HTTP status codes at all.
"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.common import PaginatedResponse
from app.schemas.auth import CurrentUser
from app.services import product_service
from app.utils.deps import get_current_user, require_role
from app.models.enums import UserRole

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or product code"),
    category: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = product_service.list_products(db, page, page_size, search, category, active)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER)),
):
    try:
        product = product_service.create_product(db, payload.model_dump())
        db.commit()
        db.refresh(product)
        return product
    except product_service.DuplicateProductCodeError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product code '{e}' already exists")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        return product_service.get_product(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER)),
):
    try:
        changes = payload.model_dump(exclude_unset=True)
        product = product_service.update_product(db, product_id, changes)
        db.commit()
        db.refresh(product)
        return product
    except product_service.ProductNotFoundError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
):
    """Soft-delete: sets active=False. See product_service docstring
    for why this is the default DELETE behavior instead of a hard delete."""
    try:
        product_service.deactivate_product(db, product_id)
        db.commit()
        return {"message": "Product deactivated"}
    except product_service.ProductNotFoundError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
