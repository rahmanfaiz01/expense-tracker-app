"""Dashboard aggregations built on top of the report queries."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.crud import report as report_crud
from app.models.enums import TransactionType
from app.schemas.report import CategoryTotal, MonthlyPoint, SummaryRead

UNCATEGORIZED_LABEL = "Uncategorized"
_ZERO = Decimal("0.00")
_MONTHS_IN_YEAR = 12


def summary(
    db: Session,
    *,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SummaryRead:
    """Total income, total expenses and the resulting balance."""
    totals = report_crud.totals_by_type(db, user_id=user_id, date_from=date_from, date_to=date_to)
    income = totals[TransactionType.INCOME]
    expenses = totals[TransactionType.EXPENSE]
    return SummaryRead(
        total_income=income,
        total_expenses=expenses,
        balance=income - expenses,
        transaction_count=report_crud.transaction_count(
            db, user_id=user_id, date_from=date_from, date_to=date_to
        ),
    )


def _month_label(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _recent_months(end: date, count: int) -> list[str]:
    """Return ``count`` month labels ending with ``end``'s month, oldest first."""
    labels: list[str] = []
    year, month = end.year, end.month
    for _ in range(count):
        labels.append(_month_label(year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, _MONTHS_IN_YEAR
    return list(reversed(labels))


def monthly(
    db: Session,
    *,
    user_id: uuid.UUID,
    months: int,
    today: date | None = None,
) -> list[MonthlyPoint]:
    """Income and expenses for the last ``months`` months, oldest first.

    Months without transactions are returned as zeros so the chart keeps a
    continuous axis.
    """
    reference = today or date.today()
    labels = _recent_months(reference, months)
    first_label = labels[0]
    start = date(int(first_label[:4]), int(first_label[5:]), 1)

    rows = {
        month: (income, expenses)
        for month, income, expenses in report_crud.monthly_totals(
            db, user_id=user_id, date_from=start
        )
    }
    points: list[MonthlyPoint] = []
    for label in labels:
        income, expenses = rows.get(label, (_ZERO, _ZERO))
        points.append(
            MonthlyPoint(month=label, income=income, expenses=expenses, net=income - expenses)
        )
    return points


def by_category(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: TransactionType,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[CategoryTotal]:
    """Totals grouped by category, largest first, with an uncategorized bucket."""
    rows = report_crud.totals_by_category(
        db, user_id=user_id, type_=type_, date_from=date_from, date_to=date_to
    )
    return [
        CategoryTotal(
            category_id=category_id,
            category_name=name if name is not None else UNCATEGORIZED_LABEL,
            color=color,
            total=total,
            type=type_,
        )
        for category_id, name, color, total in rows
    ]
