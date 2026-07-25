"""Category ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TransactionType, transaction_type_enum
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class Category(UUIDMixin, TimestampMixin, Base):
    """A user-defined grouping for income or expense transactions.

    Deletion behavior:
    - Deleting the owning user cascades and removes the category
      (``ON DELETE CASCADE`` on ``user_id``).
    - Deleting a category sets ``transactions.category_id`` to NULL
      (``ON DELETE SET NULL``) so existing transactions remain valid.
    """

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", "type", name="uq_categories_user_name_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[TransactionType] = mapped_column(transaction_type_enum, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    user: Mapped[User] = relationship(back_populates="categories")
    transactions: Mapped[list[Transaction]] = relationship(back_populates="category")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Category id={self.id!r} name={self.name!r} type={self.type!r}>"
