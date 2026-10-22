"""
StockMovement model.

WHY this table exists: it's the immutable audit log behind every
inventory change. Inventory.quantity is a current-state snapshot;
StockMovement is the history of HOW it got there. This is what backs
the "inventory movement history" feature (Phase 13) and lets us
recompute/verify current stock independently of the Inventory table —
useful for catching bugs (e.g. Phase 17's example troubleshooting issue,
"inventory mismatch after Excel import").

reference_id is intentionally a loose pointer (not a hard FK) because
a movement's origin varies by type: an order id for SALE, an Excel
import batch id for PURCHASE, a manual correction id for ADJUSTMENT.
Making it a strict FK to one table would force awkward nullable FKs to
three different tables instead.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import MovementType


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    distributor_id = Column(Integer, ForeignKey("distributors.id"), nullable=False, index=True)
    movement_type = Column(SAEnum(MovementType, name="movement_type"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)  # positive for inbound (PURCHASE/RETURN), negative for outbound (SALE)
    reference_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    product = relationship("Product")
    distributor = relationship("Distributor")
