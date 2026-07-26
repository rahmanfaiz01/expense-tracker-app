"""Shared pytest fixtures."""

from collections.abc import Generator, Iterator

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db.session import get_db
from app.main import create_app
from app.tests.db_utils import TEST_DATABASE_URL, make_alembic_config, reset_database


@pytest.fixture(autouse=True)
def _disable_rate_limiting() -> Generator[None, None, None]:
    """Keep limits out of the way; ``test_rate_limit`` re-enables them locally."""
    limiter.enabled = False
    yield
    limiter.enabled = False


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient for the FastAPI app (health endpoint needs no DB)."""
    return TestClient(create_app())


@pytest.fixture(scope="session")
def migrated_database() -> Generator[str, None, None]:
    """Provision a fresh test database and apply all migrations once per session."""
    reset_database(TEST_DATABASE_URL)
    cfg = make_alembic_config(TEST_DATABASE_URL)
    command.upgrade(cfg, "head")
    yield TEST_DATABASE_URL


@pytest.fixture(scope="session")
def engine(migrated_database: str) -> Generator[Engine, None, None]:
    eng = create_engine(migrated_database)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """Yield a session wrapped in a transaction that is rolled back after the test.

    ``join_transaction_mode="create_savepoint"`` lets application code call
    ``commit()`` (the API endpoints do) without escaping the outer transaction,
    so every test still starts from a clean database.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """A TestClient whose requests run against the rolled-back test session."""
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
