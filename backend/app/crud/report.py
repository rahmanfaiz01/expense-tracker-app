"""Aggregate queries backing the dashboard and report endpoints.

All aggregation happens in PostgreSQL: summing thousands of rows in Python
would be both slower and risk losing ``Decimal`` exactness.
"""

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement, Numeric, cast, func, select
from sqlalchemy.orm import Session

from app.models import Category, Transaction
from app.models.enums import TransactionType

_ZERO = Decimal("0.00")
_MONTH_FORMAT = "YYYY-MM"


def _scoped(
    user_id: uuid.UUID, date_from: date | None, date_to: date | None
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Transaction.user_id == user_id]
    if date_from is not None:
        conditions.append(Transaction.occurred_on >= date_from)
    if date_to is not None:
        conditions.append(Transaction.occurred_on <= date_to)
    return conditions


def totals_by_type(
    db: Session,
    *,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[TransactionType, Decimal]:
    """Return the summed amount per transaction type (missing types are zero)."""
    stmt = (
        select(Transaction.type, func.sum(Transaction.amount))
        .where(*_scoped(user_id, date_from, date_to))
        .group_by(Transaction.type)
    )
    totals = dict.fromkeys(TransactionType, _ZERO)
    for type_, total in db.execute(stmt).all():
        totals[type_] = total if total is not None else _ZERO
    return totals


def transaction_count(
    db: Session,
    *,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    """Count the user's transactions in the period."""
    stmt = select(func.count(Transaction.id)).where(*_scoped(user_id, date_from, date_to))
    return db.execute(stmt).scalar_one()


def monthly_totals(
    db: Session,
    *,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Sequence[tuple[str, Decimal, Decimal]]:
    """Return ``(month, income, expenses)`` rows ordered oldest first.

    ``month`` is a ``YYYY-MM`` label; months without transactions are absent and
    are filled in by the service layer so charts show a continuous axis.
    """
    month = func.to_char(Transaction.occurred_on, _MONTH_FORMAT).label("month")
    income = func.coalesce(
        func.sum(Transaction.amount).filter(Transaction.type == TransactionType.INCOME),
        cast(0, Numeric(12, 2)),
    )
    expenses = func.coalesce(
        func.sum(Transaction.amount).filter(Transaction.type == TransactionType.EXPENSE),
        cast(0, Numeric(12, 2)),
    )
    stmt = (
        select(month, income, expenses)
        .where(*_scoped(user_id, date_from, date_to))
        .group_by(month)
        .order_by(month)
    )
    return [(row[0], row[1], row[2]) for row in db.execute(stmt).all()]


def totals_by_category(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: TransactionType,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Sequence[tuple[uuid.UUID | None, str | None, str | None, Decimal]]:
    """Return ``(category_id, name, color, total)`` rows, largest total first.

    Transactions whose category was deleted are grouped into a single row with a
    ``None`` id so the totals still add up to the period's expenses.
    """
    total = func.sum(Transaction.amount).label("total")
    stmt = (
        select(Category.id, Category.name, Category.color, total)
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*_scoped(user_id, date_from, date_to), Transaction.type == type_)
        .group_by(Category.id, Category.name, Category.color)
        .order_by(total.desc())
    )
    return [(row[0], row[1], row[2], row[3]) for row in db.execute(stmt).all()]
