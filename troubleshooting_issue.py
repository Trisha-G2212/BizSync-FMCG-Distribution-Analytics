"""
TroubleshootingIssue model.

WHY this is its own standalone table (no FK to orders/products/etc.):
operational issues can be about ANYTHING in the system — a data import,
a UI bug, a performance problem — not just one entity type. `module` is
a free-text label (e.g. "Excel Import", "Inventory") rather than a FK,
matching how a real internal issue tracker works: the issue references
a subsystem by name, not a specific database row.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import IssueSeverity, IssueStatus


class TroubleshootingIssue(Base):
    __tablename__ = "troubleshooting_issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SAEnum(IssueSeverity, name="issue_severity"), nullable=False, index=True)
    module = Column(String(80), nullable=False, index=True)
    status = Column(SAEnum(IssueStatus, name="issue_status"), nullable=False, default=IssueStatus.OPEN, index=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    root_cause = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
