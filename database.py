"""
SQLAlchemy engine + session management.

WHY: FastAPI is request-scoped but SQLAlchemy sessions are NOT thread-safe
to share across requests. `get_db()` is a dependency that hands each
request its own Session and guarantees it's closed afterward, even if
the request raises an exception. This is the standard FastAPI+SQLAlchemy
pattern and prevents connection leaks under load.

INTERVIEW ANSWER: "How does the backend talk to PostgreSQL?"
-> "SQLAlchemy's engine manages a connection pool to Postgres. Each
   request gets a fresh Session via dependency injection (`Depends(get_db)`),
   used for that request's queries, then closed in a `finally` block."
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
