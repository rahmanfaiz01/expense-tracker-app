"""Shared Pydantic base classes and validators."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response schemas that are populated from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


def normalize_currency(value: str) -> str:
    """Normalize and validate a 3-letter ISO-4217-style currency code.

    Strips surrounding whitespace and upper-cases the value, then enforces
    exactly three ASCII letters (A-Z).
    """
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
        raise ValueError("currency must be a three-letter code (e.g. 'USD')")
    return normalized
