"""Transaction Pydantic schemas."""

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
