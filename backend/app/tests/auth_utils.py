"""Helpers shared by the authentication tests."""

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.core.config import settings

PASSWORD = "correct-horse-9"


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex}@example.com"


def register(
    client: TestClient,
    email: str | None = None,
    password: str = PASSWORD,
    full_name: str | None = "Test User",
) -> tuple[str, dict[str, Any]]:
    """Register a user and return ``(email, response_json)``."""
    address = email or unique_email()
    response = client.post(
        "/api/v1/auth/register",
        json={"email": address, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return address, response.json()


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def refresh_cookie(client: TestClient) -> str | None:
    """Return the refresh-token value currently held by the client."""
    return client.cookies.get(settings.REFRESH_COOKIE_NAME)


def set_refresh_cookie(client: TestClient, value: str) -> None:
    """Seed the cookie jar exactly as the server would (same domain and path)."""
    client.cookies.set(
        settings.REFRESH_COOKIE_NAME,
        value,
        domain="testserver.local",
        path=settings.REFRESH_COOKIE_PATH,
    )
