"""Refresh-token rotation, reuse detection and revocation tests."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_refresh_token
from app.crud import user as user_crud
from app.models import RefreshToken
from app.services.auth import INVALID_TOKEN
from app.tests.auth_utils import refresh_cookie, register, set_refresh_cookie


def _stored(db: Session, raw_token: str) -> RefreshToken:
    token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    ).scalar_one()
    return token


def test_refresh_rotates_token_and_returns_new_access_token(
    api_client: TestClient, db_session: Session
) -> None:
    register(api_client)
    original = refresh_cookie(api_client)
    assert original is not None

    response = api_client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    rotated = refresh_cookie(api_client)
    assert rotated is not None
    assert rotated != original
    assert response.json()["access_token"]

    old_token = _stored(db_session, original)
    new_token = _stored(db_session, rotated)
    assert old_token.revoked_at is not None
    assert new_token.revoked_at is None
    assert new_token.family_id == old_token.family_id


def test_raw_refresh_token_is_never_stored(api_client: TestClient, db_session: Session) -> None:
    register(api_client)
    raw = refresh_cookie(api_client)
    assert raw is not None

    hashes = db_session.execute(select(RefreshToken.token_hash)).scalars().all()
    assert raw not in hashes
    assert hash_refresh_token(raw) in hashes


def test_reusing_old_refresh_token_is_rejected_and_kills_family(
    api_client: TestClient, db_session: Session
) -> None:
    register(api_client)
    original = refresh_cookie(api_client)
    assert original is not None
    api_client.post("/api/v1/auth/refresh")
    rotated = refresh_cookie(api_client)
    assert rotated is not None

    set_refresh_cookie(api_client, original)
    replay = api_client.post("/api/v1/auth/refresh")

    assert replay.status_code == 401
    assert replay.json()["detail"] == INVALID_TOKEN

    db_session.expire_all()
    assert _stored(db_session, rotated).revoked_at is not None

    set_refresh_cookie(api_client, rotated)
    assert api_client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_without_cookie_is_rejected(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_TOKEN


def test_refresh_with_unknown_token_is_rejected(api_client: TestClient) -> None:
    set_refresh_cookie(api_client, "not-a-real-token")

    assert api_client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_with_tampered_token_is_rejected(api_client: TestClient) -> None:
    register(api_client)
    original = refresh_cookie(api_client)
    assert original is not None

    set_refresh_cookie(api_client, original[:-1] + ("A" if original[-1] != "A" else "B"))

    assert api_client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_with_expired_token_is_rejected(
    api_client: TestClient, db_session: Session
) -> None:
    register(api_client)
    raw = refresh_cookie(api_client)
    assert raw is not None
    stored = _stored(db_session, raw)
    stored.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    response = api_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    db_session.expire_all()
    assert _stored(db_session, raw).revoked_at is not None


def test_refresh_rejected_after_user_deactivated(
    api_client: TestClient, db_session: Session
) -> None:
    email, _ = register(api_client)
    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = api_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_TOKEN


def test_failed_refresh_clears_cookie(api_client: TestClient) -> None:
    set_refresh_cookie(api_client, "not-a-real-token")

    response = api_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    set_cookie = response.headers["set-cookie"]
    assert set_cookie.startswith(f'{settings.REFRESH_COOKIE_NAME}=""')
    assert refresh_cookie(api_client) in (None, "")
