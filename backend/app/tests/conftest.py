"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient for the FastAPI app.

    The health endpoint does not touch the database, so no DB setup is needed
    in Phase 0.
    """
    return TestClient(create_app())
