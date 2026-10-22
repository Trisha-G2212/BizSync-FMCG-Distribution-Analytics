from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_revenue: Decimal
    total_orders: int
    total_products: int
    total_retailers: int
    total_distributors: int
    total_inventory_units: int
    low_stock_products: int
    pending_orders: int


class SalesTrendPoint(BaseModel):
    period: str  # e.g. "2026-08-01" for daily, "2026-08" for monthly
    revenue: Decimal
    order_count: int


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    category: str
    total_quantity: int
    total_revenue: Decimal


class TopRetailer(BaseModel):
    retailer_id: int
    retailer_name: str
    total_orders: int
    total_revenue: Decimal


class CategoryPerformance(BaseModel):
    category: str
    total_revenue: Decimal
    total_quantity: int


class DistributorPerformance(BaseModel):
    distributor_id: int
    distributor_name: str
    total_revenue: Decimal
    total_orders: int
    retailer_count: int
    inventory_value: Decimal
