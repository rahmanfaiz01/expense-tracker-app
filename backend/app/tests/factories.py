"""Lightweight builders for ORM objects used in tests."""

import uuid
from datetime import date
from decimal import Decimal

from app.models import Category, Transaction, User
from app.models.enums import TransactionType


def make_user(email: str | None = None) -> User:
    return User(
        email=email or f"user-{uuid.uuid4().hex}@example.com",
        hashed_password="not-a-real-hash",
        full_name="Test User",
    )


def make_category(
    user: User,
    name: str = "Groceries",
    type_: TransactionType = TransactionType.EXPENSE,
    color: str | None = "#1A2B3C",
) -> Category:
    return Category(user=user, name=name, type=type_, color=color)


def make_transaction(
    user: User,
    category: Category | None = None,
    type_: TransactionType = TransactionType.EXPENSE,
    amount: Decimal = Decimal("12.34"),
    currency: str = "USD",
    occurred_on: date | None = None,
) -> Transaction:
    return Transaction(
        user=user,
        category=category,
        type=type_,
        amount=amount,
        currency=currency,
        description="test transaction",
        occurred_on=occurred_on or date(2026, 1, 15),
    )
