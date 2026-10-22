"""
Pytest fixtures shared across all test files.

WHY A SEPARATE TEST DATABASE (bizsync_test, not bizsync): tests need to
freely create, modify, and delete rows without any risk of corrupting
the real seeded data used for demos. TEST_DATABASE_URL (with a sensible
default) means running `pytest` can never touch the actual bizsync
database, even by accident.

WHY EACH REQUEST GETS ITS OWN FRESH SESSION (mirroring app.database.get_db
exactly, rather than forcing the whole test to share one Session):
FastAPI's TestClient runs synchronous route handlers in a worker thread,
separate from the test's own thread. SQLAlchemy Sessions are not
thread-safe, so sharing one Session object between the test and the
app's request handling caused hard-to-diagnose "transaction already
deassociated" errors. Giving every request its own session — exactly
how a real deployed server behaves — sidesteps the whole problem, and
is arguably a MORE faithful test of production behavior anyway.

WHY TABLES ARE EMPTIED (not dropped/recreated) BETWEEN TESTS: dropping
and recreating tables for every single test would be slow. Instead,
tables are created once per test session, and every table is emptied
via DELETE after each test — fast, and just as effective at preventing
one test's leftover data from affecting the next.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401 — registers all models with Base.metadata
from app.models.user import User
from app.models.enums import UserRole
from app.utils.security import hash_password

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://bizsync_user:bizsync_pass@localhost:5432/bizsync_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """A session for the TEST itself to seed/inspect data with. The
    app's own request handling uses SEPARATE sessions (see `client`
    fixture below) — both point at the same underlying database, so
    committed changes from one are visible to the other, exactly like
    two different processes talking to the same Postgres server."""
    session = TestSessionLocal()
    yield session
    session.close()
    # Empty every table so the next test starts from a clean slate.
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture()
def client(db_session):
    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    # WHY NOT "@something.test": .test is an RFC 2606 reserved
    # special-use TLD, and Pydantic's email validator correctly
    # refuses to accept it as a real address.
    user = User(
        name="Test Admin", email="test-admin@bizsync-tests.com",
        password_hash=hash_password("testpass123"), role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def analyst_user(db_session):
    user = User(
        name="Test Analyst", email="test-analyst@bizsync-tests.com",
        password_hash=hash_password("testpass123"), role=UserRole.ANALYST,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_headers(client, admin_user):
    response = client.post("/api/auth/login", json={"email": admin_user.email, "password": "testpass123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def analyst_headers(client, analyst_user):
    response = client.post("/api/auth/login", json={"email": analyst_user.email, "password": "testpass123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
