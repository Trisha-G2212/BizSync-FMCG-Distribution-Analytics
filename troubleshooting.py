from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueSeverity, IssueStatus


class IssueCreate(BaseModel):
    title: str
    description: str
    severity: IssueSeverity
    module: str
    assigned_to: Optional[int] = None


class IssueUpdate(BaseModel):
    """
    WHY status, root_cause, resolution ARE ALL OPTIONAL HERE (not a
    separate endpoint per field): the root-cause-analysis workflow the
    spec asks for — Identify -> Check logs -> Root cause -> Resolution
    -> Verify -> Close — is filled in incrementally over the life of an
    issue, not all at once. A single flexible PATCH-style update lets
    the frontend save partial progress (e.g. just the root cause, while
    still IN_PROGRESS) without needing multiple round-trip endpoints.
    """
    status: Optional[IssueStatus] = None
    severity: Optional[IssueSeverity] = None
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: IssueSeverity
    module: str
    status: IssueStatus
    reported_by: Optional[int]
    assigned_to: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]
    root_cause: Optional[str]
    resolution: Optional[str]
