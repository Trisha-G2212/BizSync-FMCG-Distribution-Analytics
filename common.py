"""
Generic paginated response wrapper.

WHY: the spec explicitly requires pagination ("do not load thousands of
records unnecessarily"). Every list endpoint (products, retailers,
orders, ...) returns this same shape so the frontend has ONE pagination
component/pattern to build, instead of a bespoke shape per endpoint.
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
