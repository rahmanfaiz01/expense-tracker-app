"""GET /users/me and access-token validation tests."""

import uuid
from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.services.auth import INVALID_TOKEN
from app.tests.auth_utils import auth_header, register


def test_me_returns_the_authenticated_user(api_client: TestClient) -> None:
    email, body = register(api_client)

    response = api_client.get("/api/v1/users/me", headers=auth_header(body["access_token"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == email
    assert payload["full_name"] == "Test User"
    assert payload["is_active"] is True
    assert set(payload) == {
        "id",
        "email",
        "full_name",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_me_requires_a_token(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_TOKEN


def test_me_rejects_malformed_and_tampered_tokens(api_client: TestClient) -> None:
    _, body = register(api_client)
    token = body["access_token"]
    head, payload, signature = token.split(".")
    tampered = f"{head}.{payload}.{signature[:-2]}xy"
    foreign = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access"},
        "a-different-signing-key-of-sufficient-length",
    )

    for candidate in ["", "not-a-jwt", tampered, foreign]:
        response = api_client.get("/api/v1/users/me", headers=auth_header(candidate))
        assert response.status_code == 401, candidate


def test_me_rejects_expired_token(api_client: TestClient, db_session: Session) -> None:
    email, _ = register(api_client)
    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    expired = create_access_token(user.id, expires_delta=timedelta(seconds=-1))

    response = api_client.get("/api/v1/users/me", headers=auth_header(expired))

    assert response.status_code == 401


def test_me_rejects_refresh_cookie_used_as_bearer_token(api_client: TestClient) -> None:
    register(api_client)
    raw_refresh = api_client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert raw_refresh is not None

    response = api_client.get("/api/v1/users/me", headers=auth_header(raw_refresh))

    assert response.status_code == 401


def test_me_rejects_token_for_unknown_user(api_client: TestClient) -> None:
    token = create_access_token(uuid.uuid4())

    assert api_client.get("/api/v1/users/me", headers=auth_header(token)).status_code == 401


def test_me_rejects_deactivated_user(api_client: TestClient, db_session: Session) -> None:
    email, body = register(api_client)
    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = api_client.get("/api/v1/users/me", headers=auth_header(body["access_token"]))

    assert response.status_code == 401


def test_tokens_isolate_users(api_client: TestClient) -> None:
    first_email, first = register(api_client)
    second_email, second = register(api_client)

    first_me = api_client.get("/api/v1/users/me", headers=auth_header(first["access_token"]))
    second_me = api_client.get("/api/v1/users/me", headers=auth_header(second["access_token"]))

    assert first_me.json()["email"] == first_email
    assert second_me.json()["email"] == second_email
    assert first_me.json()["id"] != second_me.json()["id"]
