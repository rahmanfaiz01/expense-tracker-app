"""Category data access. Every query is scoped to the owning user."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category
from app.models.enums import TransactionType


def list_for_user(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: TransactionType | None = None,
) -> Sequence[Category]:
    """Return the user's categories ordered by type then name."""
    stmt = select(Category).where(Category.user_id == user_id)
    if type_ is not None:
        stmt = stmt.where(Category.type == type_)
    stmt = stmt.order_by(Category.type, Category.name)
    return db.execute(stmt).scalars().all()


def get_for_user(db: Session, *, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
    """Return one category owned by ``user_id`` or ``None``."""
    return db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    ).scalar_one_or_none()


def get_by_name_and_type(
    db: Session,
    *,
    user_id: uuid.UUID,
    name: str,
    type_: TransactionType,
) -> Category | None:
    """Return the category matching the ``(user, name, type)`` unique key."""
    return db.execute(
        select(Category).where(
            Category.user_id == user_id,
            Category.name == name,
            Category.type == type_,
        )
    ).scalar_one_or_none()


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    name: str,
    type_: TransactionType,
    color: str | None,
) -> Category:
    """Insert a category and flush so the generated id is available."""
    category = Category(user_id=user_id, name=name, type=type_, color=color)
    db.add(category)
    db.flush()
    return category


def delete(db: Session, category: Category) -> None:
    """Delete a category; its transactions survive with ``category_id = NULL``."""
    db.delete(category)
    db.flush()
