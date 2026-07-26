"""OpenAPI contract checks for the authentication endpoints."""

from typing import Any

from fastapi.testclient import TestClient


def _schema(client: TestClient) -> dict[str, Any]:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema: dict[str, Any] = response.json()
    return schema


def test_auth_endpoints_are_documented(client: TestClient) -> None:
    paths = _schema(client)["paths"]

    assert set(paths) >= {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/users/me",
    }
    assert "post" in paths["/api/v1/auth/login"]
    assert "get" in paths["/api/v1/users/me"]


def test_documented_status_codes_match_the_implementation(client: TestClient) -> None:
    paths = _schema(client)["paths"]

    assert "201" in paths["/api/v1/auth/register"]["post"]["responses"]
    assert "200" in paths["/api/v1/auth/login"]["post"]["responses"]
    assert "204" in paths["/api/v1/auth/logout"]["post"]["responses"]


def test_auth_response_schema_exposes_token_and_user_without_secrets(client: TestClient) -> None:
    schema = _schema(client)
    auth_response = schema["components"]["schemas"]["AuthResponse"]
    user_read = schema["components"]["schemas"]["UserRead"]

    assert set(auth_response["properties"]) == {
        "access_token",
        "token_type",
        "expires_in",
        "user",
    }
    assert set(user_read["properties"]) == {
        "id",
        "email",
        "full_name",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert "hashed_password" not in user_read["properties"]
    assert "refresh_token" not in auth_response["properties"]


def test_protected_endpoint_declares_bearer_security(client: TestClient) -> None:
    schema = _schema(client)

    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert schema["paths"]["/api/v1/users/me"]["get"]["security"] == [{"HTTPBearer": []}]
