from typing import List
from pydantic import BaseModel


class RowError(BaseModel):
    row: int  # 1-indexed Excel row number (header is row 1, so first data row is 2)
    message: str


class ImportSummary(BaseModel):
    """
    WHY 'failed' = duplicates + invalid_rows rather than its own
    independently-tracked count: this mirrors the spec's own example
    numbers (965 imported, 35 failed, 12 duplicates, 23 invalid —
    12+23=35). Duplicates and invalid rows are the two DISTINCT reasons
    a row can fail; 'failed' is their total, not a third category.
    """
    records_processed: int
    successfully_imported: int
    failed: int
    duplicates: int
    invalid_rows: int
    errors: List[RowError] = []
