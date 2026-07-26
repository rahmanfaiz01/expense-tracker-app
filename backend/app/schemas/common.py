"""Shared Pydantic base classes and validators."""

from pydantic import BaseModel, ConfigDict

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128


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


def normalize_email(value: str) -> str:
    """Normalize an email address for storage and lookup.

    Pydantic's ``EmailStr`` has already validated the syntax; this trims
    surrounding whitespace and lower-cases the address so that ``User@X.com``
    and ``user@x.com`` cannot become two accounts.
    """
    return value.strip().lower()


def validate_password(value: str) -> str:
    """Enforce the password policy: length plus a letter and a digit.

    Leading/trailing whitespace is preserved (it is part of the secret); only
    the composition rules are checked.
    """
    if not PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"password must be between {PASSWORD_MIN_LENGTH} and "
            f"{PASSWORD_MAX_LENGTH} characters"
        )
    if not any(char.isalpha() for char in value):
        raise ValueError("password must contain at least one letter")
    if not any(char.isdigit() for char in value):
        raise ValueError("password must contain at least one digit")
    return value
