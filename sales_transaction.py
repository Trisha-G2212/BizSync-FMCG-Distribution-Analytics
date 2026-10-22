from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class SalesTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_date: date
    retailer_id: int
    distributor_id: int
    product_id: int
    quantity: int
    revenue: Decimal
    cost: Decimal
    profit: Decimal
    created_at: datetime
