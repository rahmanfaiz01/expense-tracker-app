"""Dashboard summary and report endpoint tests."""

from datetime import date

from fastapi.testclient import TestClient

from app.tests.api_utils import create_category, create_transaction, new_user


def _seed(client: TestClient, headers: dict[str, str], month: str) -> None:
    create_transaction(
        client,
        headers,
        type_="income",
        amount="2000.00",
        occurred_on=f"{month}-01",
        description="Salary",
    )
    create_transaction(
        client,
        headers,
        amount="750.50",
        occurred_on=f"{month}-05",
        description="Rent",
    )


def test_summary_totals_and_balance(api_client: TestClient) -> None:
    headers = new_user(api_client)
    this_month = date.today().strftime("%Y-%m")
    _seed(api_client, headers, this_month)

    response = api_client.get("/api/v1/reports/summary", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_income"] == "2000.00"
    assert body["total_expenses"] == "750.50"
    assert body["balance"] == "1249.50"
    assert body["transaction_count"] == 2


def test_summary_is_scoped_to_the_current_user(api_client: TestClient) -> None:
    owner = new_user(api_client)
    other = new_user(api_client)
    _seed(api_client, owner, date.today().strftime("%Y-%m"))

    body = api_client.get("/api/v1/reports/summary", headers=other).json()

    assert body["total_income"] == "0.00"
    assert body["total_expenses"] == "0.00"
    assert body["balance"] == "0.00"
    assert body["transaction_count"] == 0


def test_summary_honours_the_date_range(api_client: TestClient) -> None:
    headers = new_user(api_client)
    create_transaction(api_client, headers, amount="10.00", occurred_on="2026-01-15")
    create_transaction(api_client, headers, amount="20.00", occurred_on="2026-02-15")

    body = api_client.get(
        "/api/v1/reports/summary",
        params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
        headers=headers,
    ).json()

    assert body["total_expenses"] == "20.00"
    assert body["transaction_count"] == 1


def test_monthly_returns_a_continuous_series(api_client: TestClient) -> None:
    headers = new_user(api_client)
    this_month = date.today().strftime("%Y-%m")
    _seed(api_client, headers, this_month)

    points = api_client.get("/api/v1/reports/monthly", params={"months": 3}, headers=headers).json()

    assert len(points) == 3
    assert points[-1]["month"] == this_month
    assert points[-1]["income"] == "2000.00"
    assert points[-1]["expenses"] == "750.50"
    assert points[-1]["net"] == "1249.50"
    # months without data are zero-filled rather than missing
    assert points[0]["income"] == "0.00"


def test_by_category_groups_and_labels_uncategorized(api_client: TestClient) -> None:
    headers = new_user(api_client)
    groceries = create_category(api_client, headers, name="Groceries", color="#112233")
    create_transaction(api_client, headers, amount="40.00", category_id=groceries["id"])
    create_transaction(api_client, headers, amount="60.00", category_id=groceries["id"])
    create_transaction(api_client, headers, amount="25.00")

    rows = api_client.get("/api/v1/reports/by-category", headers=headers).json()

    assert [(row["category_name"], row["total"]) for row in rows] == [
        ("Groceries", "100.00"),
        ("Uncategorized", "25.00"),
    ]
    assert rows[0]["color"] == "#112233"
    assert rows[1]["category_id"] is None


def test_by_category_can_report_income(api_client: TestClient) -> None:
    headers = new_user(api_client)
    salary = create_category(api_client, headers, name="Salary", type_="income")
    create_transaction(
        api_client, headers, type_="income", amount="1500.00", category_id=salary["id"]
    )
    create_transaction(api_client, headers, amount="10.00")

    rows = api_client.get(
        "/api/v1/reports/by-category", params={"type": "income"}, headers=headers
    ).json()

    assert rows == [
        {
            "category_id": salary["id"],
            "category_name": "Salary",
            "color": rows[0]["color"],
            "total": "1500.00",
            "type": "income",
        }
    ]


def test_report_endpoints_require_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/reports/summary").status_code == 401
    assert api_client.get("/api/v1/reports/monthly").status_code == 401
    assert api_client.get("/api/v1/reports/by-category").status_code == 401
