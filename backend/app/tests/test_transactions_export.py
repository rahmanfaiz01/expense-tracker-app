"""CSV export tests."""

import csv
import io

from fastapi.testclient import TestClient

from app.tests.api_utils import create_category, create_transaction, new_user


def _rows(body: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(body)))


def test_export_contains_all_transactions(api_client: TestClient) -> None:
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

    response = api_client.get("/api/v1/transactions/export.csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    rows = _rows(response.text)
    assert rows[0] == ["date", "type", "category", "description", "amount", "currency"]
    assert len(rows) == 3
    assert ["2026-01-10", "expense", "Travel", "Train ticket", "30.00", "USD"] in rows
    # a transaction without a category exports an empty category cell
    assert ["2026-02-20", "expense", "", "Coffee", "4.50", "USD"] in rows


def test_export_respects_the_active_filters(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_transaction(api_client, headers, description="Coffee", occurred_on="2026-02-20")
    create_transaction(
        api_client,
        headers,
        type_="income",
        description="Salary",
        amount="1000.00",
        occurred_on="2026-03-01",
    )

    response = api_client.get(
        "/api/v1/transactions/export.csv",
        params={"type": "income", "date_from": "2026-03-01"},
        headers=headers,
    )

    rows = _rows(response.text)
    assert len(rows) == 2
    assert rows[1][1] == "income"
    assert "transactions_2026-03-01" in response.headers["content-disposition"]


def test_export_is_scoped_to_the_current_user(api_client: TestClient) -> None:
    owner = new_user(api_client)
    other = new_user(api_client)
    create_transaction(api_client, owner, description="Mine")

    response = api_client.get("/api/v1/transactions/export.csv", headers=other)

    assert _rows(response.text) == [
        ["date", "type", "category", "description", "amount", "currency"]
    ]


def test_export_requires_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/transactions/export.csv").status_code == 401
