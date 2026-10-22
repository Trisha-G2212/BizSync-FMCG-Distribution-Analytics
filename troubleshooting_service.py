"""
Troubleshooting service.

WHY resolved_at IS SET HERE, NOT SOMETHING THE FRONTEND SENDS: it
should always be "the moment the status actually became RESOLVED,"
which the server can determine authoritatively and consistently. If
the frontend sent this timestamp itself, a client with a wrong clock
or a delayed request could record a misleading resolution time — the
same reasoning as order_date/created_at being server-assigned
elsewhere in this app.

WHY MOVING BACK OUT OF RESOLVED CLEARS resolved_at: if an issue is
reopened (RESOLVED -> IN_PROGRESS, say because the fix didn't actually
work — a very real occurrence), it's no longer accurate to say it was
resolved at that earlier timestamp. This keeps the field meaningful
rather than stale.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.troubleshooting_issue import TroubleshootingIssue
from app.models.enums import IssueStatus
from app.repositories import troubleshooting_repository


class IssueNotFoundError(Exception):
    pass


def create_issue(db: Session, data: dict, reported_by: Optional[int]) -> TroubleshootingIssue:
    issue = TroubleshootingIssue(**data, reported_by=reported_by, status=IssueStatus.OPEN)
    return troubleshooting_repository.create(db, issue)


def get_issue(db: Session, issue_id: int) -> TroubleshootingIssue:
    issue = troubleshooting_repository.get_by_id(db, issue_id)
    if not issue:
        raise IssueNotFoundError(issue_id)
    return issue


def list_issues(db: Session, page, page_size, status, severity, module):
    return troubleshooting_repository.list_issues(db, page, page_size, status, severity, module)


def update_issue(db: Session, issue_id: int, changes: dict) -> TroubleshootingIssue:
    issue = get_issue(db, issue_id)

    if "status" in changes:
        new_status = changes["status"]
        if new_status == IssueStatus.RESOLVED and issue.status != IssueStatus.RESOLVED:
            changes["resolved_at"] = datetime.now(timezone.utc)
        elif new_status != IssueStatus.RESOLVED and issue.resolved_at is not None:
            changes["resolved_at"] = None

    return troubleshooting_repository.update(db, issue, changes)
