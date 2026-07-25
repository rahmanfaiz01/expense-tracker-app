"""Shared enumerations for the data layer."""

import enum

from sqlalchemy import Enum as SAEnum


class TransactionType(str, enum.Enum):
    """Type of a financial entry.

    Used by both ``Transaction.type`` and ``Category.type`` so a category can be
    associated with the kind of entries it applies to.
    """

    INCOME = "income"
    EXPENSE = "expense"


# Single shared PostgreSQL ENUM type reused by the transactions and categories
# tables. ``values_callable`` stores the lowercase values ("income"/"expense")
# rather than the enum member names. ``create_type=False`` — the type is created
# and dropped explicitly by the Alembic migration to avoid duplicate CREATE TYPE.
transaction_type_enum = SAEnum(
    TransactionType,
    name="transaction_type",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    create_type=False,
)
