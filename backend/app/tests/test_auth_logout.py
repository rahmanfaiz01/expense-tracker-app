"""Logout and cookie-clearing tests."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_refresh_token
from app.models import RefreshToken
from app.tests.auth_utils import refresh_cookie, register


def test_logout_revokes_refresh_token_and_clears_cookie(
    api_client: TestClient, db_session: Session
) -> None:
    register(api_client)
    raw = refresh_cookie(api_client)
    assert raw is not None

    response = api_client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    stored = db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw))
    ).scalar_one()
    assert stored.revoked_at is not None
    assert refresh_cookie(api_client) in (None, "")


def test_refresh_after_logout_is_rejected(api_client: TestClient) -> None:
    register(api_client)
    raw = refresh_cookie(api_client)
    assert raw is not None
    api_client.post("/api/v1/auth/logout")

    api_client.cookies.set(
        settings.REFRESH_COOKIE_NAME,
        raw,
        domain="testserver.local",
        path=settings.REFRESH_COOKIE_PATH,
    )
    assert api_client.post("/api/v1/auth/refresh").status_code == 401


def test_logout_revokes_the_whole_rotation_family(
    api_client: TestClient, db_session: Session
) -> None:
    register(api_client)
    api_client.post("/api/v1/auth/refresh")

    api_client.post("/api/v1/auth/logout")

    live = (
        db_session.execute(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))
        .scalars()
        .all()
    )
    assert live == []


def test_logout_without_cookie_succeeds(api_client: TestClient) -> None:
    assert api_client.post("/api/v1/auth/logout").status_code == 204


def test_logout_is_idempotent(api_client: TestClient) -> None:
    register(api_client)

    assert api_client.post("/api/v1/auth/logout").status_code == 204
    assert api_client.post("/api/v1/auth/logout").status_code == 204
