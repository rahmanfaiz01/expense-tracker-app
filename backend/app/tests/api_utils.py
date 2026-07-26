"""Helpers for the category, transaction and report API tests."""

from typing import Any

from fastapi.testclient import TestClient

from app.tests.auth_utils import auth_header, register


def new_user(client: TestClient) -> dict[str, str]:
    """Register a fresh user and return its Authorization header."""
    _, data = register(client)
    return auth_header(data["access_token"])


def create_category(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str = "Groceries",
    type_: str = "expense",
    color: str | None = "#1A2B3C",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": name, "type": type_, "color": color},
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def create_transaction(
    client: TestClient,
    headers: dict[str, str],
    *,
    type_: str = "expense",
    amount: str = "25.00",
    occurred_on: str = "2026-03-15",
    description: str | None = "Coffee beans",
    category_id: str | None = None,
    currency: str = "USD",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": type_,
        "amount": amount,
        "occurred_on": occurred_on,
        "description": description,
        "currency": currency,
        "category_id": category_id,
    }
    response = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body
