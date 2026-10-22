from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    distributor_id: int
    quantity: int
    reserved_quantity: int
    last_updated: datetime

    @computed_field
    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


class StockAdjustment(BaseModel):
    """Manual stock correction — quantity is the DELTA (can be negative),
    not the new absolute value. This mirrors how the ADJUSTMENT movement
    type is meant to be used (see StockMovement model docstring)."""
    quantity_delta: int
    reason: str
