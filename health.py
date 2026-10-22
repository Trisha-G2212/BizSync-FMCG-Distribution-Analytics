"""
Health/system router.

This is intentionally the first router built: it proves the whole
plumbing (main.py -> routers -> database.py -> engine) is wired
correctly before any business logic is added on top, in Phase 2+.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["System"])


@router.get("/health")
def health_check():
    """Liveness probe — does the API process itself respond."""
    return {"status": "ok", "service": "bizsync-api"}


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Readiness probe — can the API actually reach PostgreSQL."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
