from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import RetailerStatus


class RetailerBase(BaseModel):
    retailer_code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    owner_name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=7, max_length=20)
    city: str = Field(..., min_length=1, max_length=80)
    state: str = Field(..., min_length=1, max_length=80)
    distributor_id: int
    status: RetailerStatus = RetailerStatus.ACTIVE


class RetailerCreate(RetailerBase):
    pass


class RetailerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    city: Optional[str] = Field(None, min_length=1, max_length=80)
    state: Optional[str] = Field(None, min_length=1, max_length=80)
    distributor_id: Optional[int] = None
    status: Optional[RetailerStatus] = None


class RetailerResponse(RetailerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
