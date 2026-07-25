"""Category Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransactionType
from app.schemas.common import ORMModel

_HEX_COLOR_LEN = 7


def _validate_color(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if (
        len(normalized) != _HEX_COLOR_LEN
        or not normalized.startswith("#")
        or not all(c in "0123456789abcdefABCDEF" for c in normalized[1:])
    ):
        raise ValueError("color must be a hex code like '#1A2B3C'")
    return normalized.upper()


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: TransactionType
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return _validate_color(value)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: TransactionType | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return _validate_color(value)


class CategoryRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: TransactionType
    color: str | None
    created_at: datetime
    updated_at: datetime
