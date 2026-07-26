"""Login endpoint tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import user as user_crud
from app.services.auth import INVALID_CREDENTIALS
from app.tests.auth_utils import PASSWORD, register, unique_email


def _login(client: TestClient, email: str, password: str = PASSWORD) -> object:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_returns_access_token_and_cookie(api_client: TestClient) -> None:
    email, _ = register(api_client)
    api_client.cookies.clear()

    response = api_client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == email
    assert api_client.cookies.get(settings.REFRESH_COOKIE_NAME)


def test_login_accepts_differently_cased_email(api_client: TestClient) -> None:
    email, _ = register(api_client)

    response = api_client.post(
        "/api/v1/auth/login", json={"email": email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 200


def test_login_rejects_wrong_password(api_client: TestClient) -> None:
    email, _ = register(api_client)

    response = api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password-1"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS
    assert settings.REFRESH_COOKIE_NAME not in response.cookies


def test_login_rejects_unknown_email_with_same_message(api_client: TestClient) -> None:
    email, _ = register(api_client)

    unknown = api_client.post(
        "/api/v1/auth/login", json={"email": unique_email(), "password": PASSWORD}
    )
    wrong_password = api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password-1"}
    )

    assert unknown.status_code == wrong_password.status_code == 401
    assert unknown.json() == wrong_password.json()


def test_login_rejects_inactive_user(api_client: TestClient, db_session: Session) -> None:
    email, _ = register(api_client)
    user = user_crud.get_by_email(db_session, email)
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = api_client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS


def test_login_requires_valid_payload(api_client: TestClient) -> None:
    assert api_client.post("/api/v1/auth/login", json={"email": "x"}).status_code == 422
