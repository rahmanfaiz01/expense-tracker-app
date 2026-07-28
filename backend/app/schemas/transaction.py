"""Transaction Pydantic schemas."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransactionType
from app.schemas.common import ORMModel, normalize_currency


class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = "USD"
    description: str | None = Field(default=None, max_length=255)
    occurred_on: date
    category_id: uuid.UUID | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = None
    description: str | None = Field(default=None, max_length=255)
    occurred_on: date | None = None
    category_id: uuid.UUID | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_currency(value)


class TransactionRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID | None
    type: TransactionType
    amount: Decimal
    currency: str
    description: str | None
    occurred_on: date
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None


class TransactionSort(str, enum.Enum):
    """Sortable transaction columns."""

    OCCURRED_ON = "occurred_on"
    AMOUNT = "amount"
    CREATED_AT = "created_at"
    DESCRIPTION = "description"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class TransactionFilters(BaseModel):
    """Search, filter and sort options shared by the list and CSV endpoints."""

    q: str | None = None
    type: TransactionType | None = None
    category_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    sort: TransactionSort = TransactionSort.OCCURRED_ON
    order: SortOrder = SortOrder.DESC


class TransactionPage(BaseModel):
    """One page of transactions plus the counters the table UI needs."""

    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
    pages: int
