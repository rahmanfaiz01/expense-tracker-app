"""Dashboard and report response schemas."""

import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import TransactionType


class SummaryRead(BaseModel):
    """Headline figures for the dashboard cards."""

    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    transaction_count: int


class MonthlyPoint(BaseModel):
    """One month of the income/expense chart."""

    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class CategoryTotal(BaseModel):
    """One slice of the by-category breakdown.

    ``category_id`` is ``None`` for transactions whose category was deleted.
    """

    category_id: uuid.UUID | None
    category_name: str
    color: str | None
    total: Decimal
    type: TransactionType
