"""
Product schemas.

WHY SEPARATE Create/Update/Response SCHEMAS instead of one:
- ProductCreate requires every field the database needs.
- ProductUpdate makes every field OPTIONAL, since a PUT/PATCH might
  only change the price, not resend the whole product.
- ProductResponse adds `id` and `created_at` — fields the CLIENT never
  sends but the SERVER always returns. Reusing one schema for all three
  purposes would either make `id` required on create (wrong — the DB
  assigns it) or make every field optional on create (wrong — that
  silently allows incomplete products).

Field-level validation (e.g. unit_price > 0) happens here via Pydantic,
enforcing it before a request even reaches business logic — this is the
"frontend AND backend validation" requirement from the spec: even if a
malicious or buggy client skips frontend checks, the API itself refuses
bad data.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=60)
    brand: str = Field(..., min_length=1, max_length=80)
    unit_price: Decimal = Field(..., gt=0)
    cost_price: Decimal = Field(..., gt=0)
    reorder_level: int = Field(default=20, ge=0)
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=60)
    brand: Optional[str] = Field(None, min_length=1, max_length=80)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, gt=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
