from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.enums import DistributorStatus


class DistributorBase(BaseModel):
    distributor_code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    contact_person: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    city: str = Field(..., min_length=1, max_length=80)
    state: str = Field(..., min_length=1, max_length=80)
    status: DistributorStatus = DistributorStatus.ACTIVE


class DistributorCreate(DistributorBase):
    pass


class DistributorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    contact_person: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(None, min_length=1, max_length=80)
    state: Optional[str] = Field(None, min_length=1, max_length=80)
    status: Optional[DistributorStatus] = None


class DistributorResponse(DistributorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class DistributorPerformance(BaseModel):
    """Aggregated metrics — computed via SQL, not stored as columns.
    See dashboard router (Phase 4 analytics) for the query."""
    distributor_id: int
    distributor_name: str
    total_revenue: float
    total_orders: int
    retailer_count: int
    inventory_value: float
