"""Category CRUD endpoint tests."""

import uuid

from fastapi.testclient import TestClient

from app.tests.api_utils import create_category, create_transaction, new_user


def test_create_and_read_category(api_client: TestClient) -> None:
    headers = new_user(api_client)

    created = create_category(api_client, headers, name="Salary", type_="income", color="#0a0b0c")
    assert created["name"] == "Salary"
    assert created["type"] == "income"
    assert created["color"] == "#0A0B0C"  # normalized to upper case

    response = api_client.get(f"/api/v1/categories/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_list_returns_only_own_categories(api_client: TestClient) -> None:
    first = new_user(api_client)
    second = new_user(api_client)
    create_category(api_client, first, name="Rent")
    create_category(api_client, second, name="Fuel")

    response = api_client.get("/api/v1/categories", headers=first)

    assert response.status_code == 200
    assert [category["name"] for category in response.json()] == ["Rent"]


def test_list_can_filter_by_type(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_category(api_client, headers, name="Salary", type_="income")
    create_category(api_client, headers, name="Rent", type_="expense")

    response = api_client.get("/api/v1/categories", params={"type": "income"}, headers=headers)

    assert [category["name"] for category in response.json()] == ["Salary"]


def test_duplicate_name_and_type_is_rejected(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_category(api_client, headers, name="Rent")

    response = api_client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Rent", "type": "expense"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A category with this name and type already exists"


def test_same_name_with_other_type_is_allowed(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_category(api_client, headers, name="Bonus", type_="expense")

    response = api_client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Bonus", "type": "income"},
    )

    assert response.status_code == 201


def test_update_category(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers, name="Groceries")

    response = api_client.patch(
        f"/api/v1/categories/{category['id']}",
        headers=headers,
        json={"name": "Food", "color": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Food"
    assert body["color"] is None
    assert body["type"] == "expense"


def test_update_to_existing_name_conflicts(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_category(api_client, headers, name="Rent")
    other = create_category(api_client, headers, name="Fuel")

    response = api_client.patch(
        f"/api/v1/categories/{other['id']}", headers=headers, json={"name": "Rent"}
    )

    assert response.status_code == 409


def test_delete_category_keeps_transactions(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers)
    transaction = create_transaction(api_client, headers, category_id=category["id"])

    deleted = api_client.delete(f"/api/v1/categories/{category['id']}", headers=headers)
    assert deleted.status_code == 204

    remaining = api_client.get(f"/api/v1/transactions/{transaction['id']}", headers=headers)
    assert remaining.status_code == 200
    assert remaining.json()["category_id"] is None


def test_other_users_category_is_not_found(api_client: TestClient) -> None:
    owner = new_user(api_client)
    intruder = new_user(api_client)
    category = create_category(api_client, owner)

    for method in ("get", "delete"):
        response = getattr(api_client, method)(
            f"/api/v1/categories/{category['id']}", headers=intruder
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"

    patched = api_client.patch(
        f"/api/v1/categories/{category['id']}", headers=intruder, json={"name": "Hijacked"}
    )
    assert patched.status_code == 404


def test_unknown_category_returns_404(api_client: TestClient) -> None:
    headers = new_user(api_client)

    response = api_client.get(f"/api/v1/categories/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


def test_category_endpoints_require_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/categories").status_code == 401
    created = api_client.post("/api/v1/categories", json={"name": "X", "type": "expense"})
    assert created.status_code == 401


def test_invalid_color_is_rejected(api_client: TestClient) -> None:
    headers = new_user(api_client)

    response = api_client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Bad", "type": "expense", "color": "red"},
    )

    assert response.status_code == 422
