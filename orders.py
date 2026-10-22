import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.schemas.common import PaginatedResponse
from app.schemas.auth import CurrentUser
from app.models.enums import OrderStatus
from app.services import order_service
from app.utils.deps import get_current_user, require_role
from app.models.enums import UserRole

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    retailer_id: Optional[int] = Query(None),
    distributor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = order_service.list_orders(db, page, page_size, status_filter, retailer_id, distributor_id)
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER, UserRole.SALES_REP)),
):
    try:
        order = order_service.create_order(
            db, payload.retailer_id, payload.distributor_id,
            [item.model_dump() for item in payload.items],
        )
        db.commit()
        db.refresh(order)
        return order
    except order_service.InvalidRetailerError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Retailer {e} does not exist")
    except order_service.InvalidDistributorError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Distributor {e} does not exist")
    except order_service.InvalidProductError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Product {e} does not exist or is inactive")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order number collision — please retry")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        return order_service.get_order(db, order_id)
    except order_service.OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER)),
):
    """
    WHY THIS ENTIRE ENDPOINT IS ONE ATOMIC UNIT: the service function
    it calls may lock rows, validate stock, deduct inventory, and write
    StockMovement records — all before this router ever calls
    db.commit(). If ANYTHING fails partway through (insufficient stock,
    an invalid transition, an unexpected error), the except block below
    calls db.rollback(), which undoes every write attempted inside the
    service call, including any row locks. The database is guaranteed
    to end up in one of exactly two states: fully updated, or
    completely unchanged. There is no partial state possible.
    """
    try:
        order = order_service.update_order_status(db, order_id, payload.status)
        db.commit()
        db.refresh(order)
        return order
    except order_service.OrderNotFoundError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except order_service.InvalidOrderTransitionError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot move order from {e.current.value} to {e.target.value}",
        )
    except order_service.InsufficientInventoryError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient inventory for product {e.product_id}: {e.available} available, {e.requested} requested",
        )
