"""Tests for Pydantic schema validation."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import TransactionType
from app.schemas import (
    CategoryCreate,
    TransactionCreate,
    TransactionRead,
    UserCreate,
)


def _txn_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "type": "expense",
        "amount": Decimal("10.00"),
        "occurred_on": date(2026, 1, 1),
    }
    base.update(overrides)
    return base


def test_currency_is_normalized_to_upper() -> None:
    txn = TransactionCreate(**_txn_kwargs(currency="usd"))
    assert txn.currency == "USD"


def test_currency_defaults_to_usd() -> None:
    txn = TransactionCreate(**_txn_kwargs())
    assert txn.currency == "USD"


@pytest.mark.parametrize("bad", ["US", "USDD", "12A", "u$d"])
def test_currency_invalid_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**_txn_kwargs(currency=bad))


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-1.00")])
def test_amount_must_be_positive(bad: Decimal) -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**_txn_kwargs(amount=bad))


def test_amount_too_many_decimal_places_rejected() -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**_txn_kwargs(amount=Decimal("1.234")))


def test_transaction_type_enum_parsed() -> None:
    txn = TransactionCreate(**_txn_kwargs(type="income"))
    assert txn.type is TransactionType.INCOME


def test_transaction_type_invalid_rejected() -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(**_txn_kwargs(type="transfer"))


def test_user_email_and_password_validation() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="longenough1")
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short1")
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="longenough")
    user = UserCreate(email=" A@B.com ", password="longenough1")
    assert user.email == "a@b.com"


def test_category_color_validation() -> None:
    ok = CategoryCreate(name="Food", type="expense", color="#1a2b3c")
    assert ok.color == "#1A2B3C"
    with pytest.raises(ValidationError):
        CategoryCreate(name="Food", type="expense", color="red")


def test_transaction_read_from_attributes() -> None:
    now = datetime.now(timezone.utc)

    class _Obj:
        id = uuid.uuid4()
        user_id = uuid.uuid4()
        category_id = None
        type = TransactionType.EXPENSE
        amount = Decimal("5.00")
        currency = "USD"
        description = None
        occurred_on = date(2026, 1, 1)
        created_at = now
        updated_at = now

    read = TransactionRead.model_validate(_Obj())
    assert read.amount == Decimal("5.00")
    assert read.type is TransactionType.EXPENSE
