"""
Creates every table defined by the SQLAlchemy models.

WHY create_all() INSTEAD OF ALEMBIC MIGRATIONS: Alembic is the correct
tool for a real production app with evolving schemas over time, but it
adds real complexity (migration scripts, version history) that isn't
worth it for a student project where the schema is being designed
once, up front. create_all() is explicitly documented by SQLAlchemy as
fine for this use case: it creates tables that don't exist yet and
never touches tables that already exist, so re-running this script is
always safe.

INTERVIEW ANSWER: "How do you manage schema changes?" -> "For this
project, the schema is created directly from the SQLAlchemy models via
create_all(). In a real production system with a live, evolving schema,
I'd use Alembic to generate versioned, reversible migrations instead."

Usage:
    python -m app.create_tables
"""
from app.database import engine, Base
from app import models  # noqa: F401  (import triggers model registration)


def create_all_tables():
    print(f"Creating tables on: {engine.url.render_as_string(hide_password=True)}")
    Base.metadata.create_all(bind=engine)
    table_names = sorted(Base.metadata.tables.keys())
    print(f"Done. {len(table_names)} tables ensured:")
    for name in table_names:
        print(f"  - {name}")


if __name__ == "__main__":
    create_all_tables()
