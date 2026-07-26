"""Rate limiting on the authentication endpoints."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import TOO_MANY_REQUESTS, limiter
from app.tests.auth_utils import PASSWORD, unique_email


@pytest.fixture()
def strict_limits() -> Generator[None, None, None]:
    """Enable the limiter with a tiny login budget, then restore the defaults."""
    original = settings.RATE_LIMIT_LOGIN
    settings.RATE_LIMIT_LOGIN = "2/minute"
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()
    settings.RATE_LIMIT_LOGIN = original


@pytest.mark.usefixtures("strict_limits")
def test_login_is_rate_limited(api_client: TestClient) -> None:
    payload = {"email": unique_email(), "password": PASSWORD}

    statuses = [api_client.post("/api/v1/auth/login", json=payload).status_code for _ in range(3)]

    assert statuses == [401, 401, 429]


@pytest.mark.usefixtures("strict_limits")
def test_rate_limited_response_is_generic(api_client: TestClient) -> None:
    payload = {"email": unique_email(), "password": PASSWORD}
    for _ in range(3):
        response = api_client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 429
    assert response.json()["detail"] == TOO_MANY_REQUESTS


def test_limits_are_disabled_for_the_rest_of_the_suite(api_client: TestClient) -> None:
    payload = {"email": unique_email(), "password": PASSWORD}

    statuses = {api_client.post("/api/v1/auth/login", json=payload).status_code for _ in range(12)}

    assert statuses == {401}
