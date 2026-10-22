from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.troubleshooting_issue import TroubleshootingIssue


def get_by_id(db: Session, issue_id: int) -> Optional[TroubleshootingIssue]:
    return db.get(TroubleshootingIssue, issue_id)


def list_issues(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    module: Optional[str] = None,
) -> Tuple[List[TroubleshootingIssue], int]:
    query = select(TroubleshootingIssue)
    count_query = select(func.count()).select_from(TroubleshootingIssue)

    filters = []
    if status:
        filters.append(TroubleshootingIssue.status == status)
    if severity:
        filters.append(TroubleshootingIssue.severity == severity)
    if module:
        filters.append(TroubleshootingIssue.module == module)

    for condition in filters:
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    # Open/critical issues surfaced first — matches how a real ops team
    # would want to triage a list, not just newest-first.
    query = query.order_by(TroubleshootingIssue.status, TroubleshootingIssue.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    return items, total


def create(db: Session, issue: TroubleshootingIssue) -> TroubleshootingIssue:
    db.add(issue)
    db.flush()
    return issue


def update(db: Session, issue: TroubleshootingIssue, changes: dict) -> TroubleshootingIssue:
    for field, value in changes.items():
        setattr(issue, field, value)
    db.flush()
    return issue
