"""Registration endpoint tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.crud import user as user_crud
from app.services.auth import REGISTRATION_FAILED
from app.tests.auth_utils import PASSWORD, register, unique_email


def test_register_creates_user_and_logs_in(api_client: TestClient, db_session: Session) -> None:
    email, body = register(api_client)

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert body["user"]["email"] == email
    assert body["user"]["is_active"] is True
    assert "password" not in body["user"]
    assert "hashed_password" not in body["user"]

    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    assert user.full_name == "Test User"


def test_register_stores_argon2_hash_not_plaintext(
    api_client: TestClient, db_session: Session
) -> None:
    email, _ = register(api_client)

    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("$argon2id$")
    assert verify_password(PASSWORD, user.hashed_password)
    assert not verify_password("not-the-password-1", user.hashed_password)


def test_register_sets_refresh_cookie(api_client: TestClient) -> None:
    register(api_client)
    assert api_client.cookies.get(settings.REFRESH_COOKIE_NAME)


def test_register_rejects_duplicate_email(api_client: TestClient) -> None:
    email, _ = register(api_client)

    response = api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Impostor"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == REGISTRATION_FAILED


def test_register_normalizes_email_case(api_client: TestClient, db_session: Session) -> None:
    email = unique_email()

    register(api_client, email=email.upper())

    assert user_crud.get_by_email(db_session, email) is not None


def test_register_rejects_duplicate_email_differing_only_in_case(api_client: TestClient) -> None:
    email = unique_email()
    register(api_client, email=email)

    response = api_client.post(
        "/api/v1/auth/register",
        json={"email": email.upper(), "password": PASSWORD},
    )

    assert response.status_code == 409


def test_register_rejects_invalid_email(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": PASSWORD},
    )
    assert response.status_code == 422


def test_register_enforces_password_policy(api_client: TestClient) -> None:
    for weak in ["short1", "nodigitspassword", "1234567890"]:
        response = api_client.post(
            "/api/v1/auth/register",
            json={"email": unique_email(), "password": weak},
        )
        assert response.status_code == 422, weak
