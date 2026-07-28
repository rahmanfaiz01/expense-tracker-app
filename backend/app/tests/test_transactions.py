"""Transaction CRUD, search, filter, sort and pagination tests."""

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from app.tests.api_utils import create_category, create_transaction, new_user


def test_create_transaction_with_category(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers, name="Groceries")

    created = create_transaction(api_client, headers, amount="12.34", category_id=category["id"])

    assert created["amount"] == "12.34"
    assert Decimal(created["amount"]) == Decimal("12.34")
    assert created["category_id"] == category["id"]
    assert created["category_name"] == "Groceries"
    assert created["currency"] == "USD"


def test_create_normalizes_currency_and_rejects_bad_amounts(api_client: TestClient) -> None:
    headers = new_user(api_client)

    normalized = create_transaction(api_client, headers, currency=" eur ")
    assert normalized["currency"] == "EUR"

    for amount in ("0", "-1.00"):
        response = api_client.post(
            "/api/v1/transactions",
            headers=headers,
            json={"type": "expense", "amount": amount, "occurred_on": "2026-03-01"},
        )
        assert response.status_code == 422


def test_category_must_match_transaction_type(api_client: TestClient) -> None:
    headers = new_user(api_client)
    income_category = create_category(api_client, headers, name="Salary", type_="income")

    response = api_client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "type": "expense",
            "amount": "10.00",
            "occurred_on": "2026-03-01",
            "category_id": income_category["id"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Category type does not match the transaction type"


def test_cannot_use_another_users_category(api_client: TestClient) -> None:
    owner = new_user(api_client)
    intruder = new_user(api_client)
    category = create_category(api_client, owner)

    response = api_client.post(
        "/api/v1/transactions",
        headers=intruder,
        json={
            "type": "expense",
            "amount": "10.00",
            "occurred_on": "2026-03-01",
            "category_id": category["id"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_list_is_scoped_to_the_current_user(api_client: TestClient) -> None:
    first = new_user(api_client)
    second = new_user(api_client)
    create_transaction(api_client, first, description="Mine")
    create_transaction(api_client, second, description="Theirs")

    response = api_client.get("/api/v1/transactions", headers=first)

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "Mine"


def test_search_filters_and_sorting(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers, name="Travel")
    create_transaction(
        api_client,
        headers,
        description="Train ticket",
        amount="30.00",
        occurred_on="2026-01-10",
        category_id=category["id"],
    )
    create_transaction(
        api_client, headers, description="Coffee", amount="4.50", occurred_on="2026-02-20"
    )
    create_transaction(
        api_client,
        headers,
        type_="income",
        description="Salary payment",
        amount="1000.00",
        occurred_on="2026-03-01",
    )

    search = api_client.get("/api/v1/transactions", params={"q": "train"}, headers=headers)
    assert [item["description"] for item in search.json()["items"]] == ["Train ticket"]

    by_type = api_client.get("/api/v1/transactions", params={"type": "income"}, headers=headers)
    assert by_type.json()["total"] == 1

    by_category = api_client.get(
        "/api/v1/transactions", params={"category_id": category["id"]}, headers=headers
    )
    assert by_category.json()["total"] == 1

    by_date = api_client.get(
        "/api/v1/transactions",
        params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
        headers=headers,
    )
    assert [item["description"] for item in by_date.json()["items"]] == ["Coffee"]

    sorted_amounts = api_client.get(
        "/api/v1/transactions",
        params={"sort": "amount", "order": "asc"},
        headers=headers,
    )
    assert [item["amount"] for item in sorted_amounts.json()["items"]] == [
        "4.50",
        "30.00",
        "1000.00",
    ]


def test_search_treats_wildcards_literally(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_transaction(api_client, headers, description="100% cotton")
    create_transaction(api_client, headers, description="Plain text")

    response = api_client.get("/api/v1/transactions", params={"q": "100%"}, headers=headers)

    assert [item["description"] for item in response.json()["items"]] == ["100% cotton"]


def test_invalid_date_range_is_rejected(api_client: TestClient) -> None:
    headers = new_user(api_client)

    response = api_client.get(
        "/api/v1/transactions",
        params={"date_from": "2026-03-02", "date_to": "2026-03-01"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "date_from must not be after date_to"


def test_pagination_metadata_and_slicing(api_client: TestClient) -> None:
    headers = new_user(api_client)
    for day in range(1, 6):
        create_transaction(
            api_client, headers, description=f"Day {day}", occurred_on=f"2026-04-0{day}"
        )

    first_page = api_client.get(
        "/api/v1/transactions",
        params={"page": 1, "page_size": 2, "sort": "occurred_on", "order": "asc"},
        headers=headers,
    ).json()
    assert first_page["total"] == 5
    assert first_page["pages"] == 3
    assert [item["description"] for item in first_page["items"]] == ["Day 1", "Day 2"]

    last_page = api_client.get(
        "/api/v1/transactions",
        params={"page": 3, "page_size": 2, "sort": "occurred_on", "order": "asc"},
        headers=headers,
    ).json()
    assert [item["description"] for item in last_page["items"]] == ["Day 5"]


def test_page_size_is_capped(api_client: TestClient) -> None:
    headers = new_user(api_client)

    response = api_client.get("/api/v1/transactions", params={"page_size": 1000}, headers=headers)

    assert response.status_code == 422


def test_update_transaction(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers, name="Groceries")
    transaction = create_transaction(api_client, headers, category_id=category["id"])

    response = api_client.patch(
        f"/api/v1/transactions/{transaction['id']}",
        headers=headers,
        json={"amount": "99.99", "description": None, "category_id": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "99.99"
    assert body["description"] is None
    assert body["category_id"] is None
    assert body["category_name"] is None


def test_update_rechecks_category_type(api_client: TestClient) -> None:
    headers = new_user(api_client)
    category = create_category(api_client, headers, name="Groceries")
    transaction = create_transaction(api_client, headers, category_id=category["id"])

    response = api_client.patch(
        f"/api/v1/transactions/{transaction['id']}", headers=headers, json={"type": "income"}
    )

    assert response.status_code == 400


def test_delete_transaction(api_client: TestClient) -> None:
    headers = new_user(api_client)
    transaction = create_transaction(api_client, headers)

    assert (
        api_client.delete(f"/api/v1/transactions/{transaction['id']}", headers=headers).status_code
        == 204
    )
    assert (
        api_client.get(f"/api/v1/transactions/{transaction['id']}", headers=headers).status_code
        == 404
    )


def test_other_users_transaction_is_not_found(api_client: TestClient) -> None:
    owner = new_user(api_client)
    intruder = new_user(api_client)
    transaction = create_transaction(api_client, owner)

    assert (
        api_client.get(f"/api/v1/transactions/{transaction['id']}", headers=intruder).status_code
        == 404
    )
    assert (
        api_client.delete(f"/api/v1/transactions/{transaction['id']}", headers=intruder).status_code
        == 404
    )


def test_unknown_transaction_returns_404(api_client: TestClient) -> None:
    headers = new_user(api_client)

    response = api_client.get(f"/api/v1/transactions/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_transaction_endpoints_require_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/transactions").status_code == 401
