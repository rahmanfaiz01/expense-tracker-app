"""Tests for ORM models: defaults, constraints, relationships, decimals, enums."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Category
from app.models.enums import TransactionType
from app.tests.factories import make_category, make_transaction, make_user


def test_user_defaults_and_uuid_pk(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    assert isinstance(user.id, uuid.UUID)
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None
    # timezone-aware timestamps
    assert user.created_at.tzinfo is not None
    assert user.updated_at.tzinfo is not None


def test_user_email_unique(db_session: Session) -> None:
    email = f"dup-{uuid.uuid4().hex}@example.com"
    db_session.add(make_user(email))
    db_session.flush()
    db_session.add(make_user(email))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_category_unique_user_name_type(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(make_category(user, name="Food", type_=TransactionType.EXPENSE))
    db_session.flush()

    # same (user, name, type) -> violation
    db_session.add(make_category(user, name="Food", type_=TransactionType.EXPENSE))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_category_same_name_different_type_allowed(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(make_category(user, name="Bonus", type_=TransactionType.EXPENSE))
    db_session.add(make_category(user, name="Bonus", type_=TransactionType.INCOME))
    db_session.flush()  # no error

    count = db_session.scalar(select(func.count()).select_from(Category))
    assert count == 2


def test_transaction_amount_must_be_positive(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(make_transaction(user, amount=Decimal("0.00")))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_currency_check_rejects_lowercase(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(make_transaction(user, currency="usd"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_decimal_is_preserved(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    txn = make_transaction(user, amount=Decimal("1234567890.12"))
    db_session.add(txn)
    db_session.flush()
    db_session.refresh(txn)

    assert isinstance(txn.amount, Decimal)
    assert txn.amount == Decimal("1234567890.12")


def test_transaction_amount_overflow_raises(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    # 12 total digits max => 11 integer digits overflow NUMERIC(12,2)
    db_session.add(make_transaction(user, amount=Decimal("99999999999.99")))
    with pytest.raises(DataError):
        db_session.flush()


def test_transaction_type_stored_as_lowercase_value(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    txn = make_transaction(user, type_=TransactionType.INCOME)
    db_session.add(txn)
    db_session.flush()

    stored = db_session.execute(
        text("SELECT type FROM transactions WHERE id = :id"), {"id": txn.id}
    ).scalar_one()
    assert stored == "income"


def test_relationships(db_session: Session) -> None:
    user = make_user()
    category = make_category(user)
    txn = make_transaction(user, category=category)
    db_session.add_all([user, category, txn])
    db_session.flush()

    assert txn.user is user
    assert txn.category is category
    assert category.user is user
    assert category in user.categories
    assert txn in user.transactions
    assert txn in category.transactions
