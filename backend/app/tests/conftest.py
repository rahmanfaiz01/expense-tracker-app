"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.main import create_app
from app.tests.db_utils import TEST_DATABASE_URL, make_alembic_config, reset_database


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

    Tests use ``session.flush()`` to trigger DB-level constraints without
    committing; teardown rolls the whole transaction back for isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
