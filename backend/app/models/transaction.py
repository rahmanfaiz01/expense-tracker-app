"""Transaction ORM model."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TransactionType, transaction_type_enum
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Transaction(UUIDMixin, TimestampMixin, Base):
    """A single income or expense entry belonging to a user.

    Deletion behavior:
    - Deleting the owning user cascades and removes the transaction
      (``ON DELETE CASCADE`` on ``user_id``).
    - Deleting the referenced category sets ``category_id`` to NULL
      (``ON DELETE SET NULL``); the transaction itself is preserved.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_format"),
        Index("ix_transactions_user_id_occurred_on", "user_id", "occurred_on"),
        Index("ix_transactions_user_id_category_id", "user_id", "category_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[TransactionType] = mapped_column(transaction_type_enum, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped[User] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship(back_populates="transactions")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"<Transaction id={self.id!r} type={self.type!r} "
            f"amount={self.amount!r} {self.currency!r}>"
        )
