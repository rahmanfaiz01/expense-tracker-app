"""Refresh-cookie attribute tests for local and cross-site configurations."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.tests.auth_utils import PASSWORD, register, unique_email


def _refresh_set_cookie(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.headers["set-cookie"]


@pytest.fixture()
def cross_site_cookies() -> Generator[None, None, None]:
    """Temporarily apply the Vercel -> Railway cookie configuration."""
    original = (settings.COOKIE_SECURE, settings.COOKIE_SAMESITE)
    settings.COOKIE_SECURE, settings.COOKIE_SAMESITE = True, "none"
    yield
    settings.COOKIE_SECURE, settings.COOKIE_SAMESITE = original


def test_refresh_cookie_is_httponly_scoped_and_lax_in_development(
    api_client: TestClient,
) -> None:
    set_cookie = _refresh_set_cookie(api_client)

    assert set_cookie.startswith(f"{settings.REFRESH_COOKIE_NAME}=")
    assert "HttpOnly" in set_cookie
    assert f"Path={settings.REFRESH_COOKIE_PATH}" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert f"Max-Age={settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60}" in set_cookie
    assert "Secure" not in set_cookie


@pytest.mark.usefixtures("cross_site_cookies")
def test_refresh_cookie_is_secure_and_samesite_none_when_configured(
    api_client: TestClient,
) -> None:
    set_cookie = _refresh_set_cookie(api_client)

    assert "Secure" in set_cookie
    assert "SameSite=none" in set_cookie
    assert "HttpOnly" in set_cookie


def test_access_token_is_only_returned_in_the_body(api_client: TestClient) -> None:
    _, body = register(api_client)

    assert body["access_token"]
    assert body["access_token"] not in "".join(api_client.cookies.values())


def test_logout_expires_the_cookie(api_client: TestClient) -> None:
    register(api_client)

    set_cookie = api_client.post("/api/v1/auth/logout").headers["set-cookie"]

    assert set_cookie.startswith(f'{settings.REFRESH_COOKIE_NAME}=""')
    assert "Max-Age=0" in set_cookie
    assert "HttpOnly" in set_cookie
    assert f"Path={settings.REFRESH_COOKIE_PATH}" in set_cookie
