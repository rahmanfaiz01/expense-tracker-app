"""Category business rules: ownership, uniqueness and validation."""

import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import category as category_crud
from app.models import Category
from app.models.enums import TransactionType
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.errors import ConflictError, NotFoundError

CATEGORY_NOT_FOUND = "Category not found"
DUPLICATE_CATEGORY = "A category with this name and type already exists"


def list_categories(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: TransactionType | None = None,
) -> Sequence[Category]:
    """Return every category owned by the user."""
    return category_crud.list_for_user(db, user_id=user_id, type_=type_)


def get_category(db: Session, *, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    """Return one owned category.

    A category belonging to another user is reported as missing rather than
    forbidden, so ids cannot be probed across accounts.
    """
    category = category_crud.get_for_user(db, user_id=user_id, category_id=category_id)
    if category is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category


def create_category(db: Session, *, user_id: uuid.UUID, payload: CategoryCreate) -> Category:
    """Create a category, rejecting a duplicate ``(name, type)`` for the user."""
    if (
        category_crud.get_by_name_and_type(
            db, user_id=user_id, name=payload.name, type_=payload.type
        )
        is not None
    ):
        raise ConflictError(DUPLICATE_CATEGORY)

    try:
        return category_crud.create(
            db,
            user_id=user_id,
            name=payload.name,
            type_=payload.type,
            color=payload.color,
        )
    except IntegrityError as exc:  # concurrent insert lost the race
        db.rollback()
        raise ConflictError(DUPLICATE_CATEGORY) from exc


def update_category(
    db: Session,
    *,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> Category:
    """Apply a partial update to an owned category."""
    category = get_category(db, user_id=user_id, category_id=category_id)
    changes = payload.model_dump(exclude_unset=True)

    name = payload.name if payload.name is not None else category.name
    type_ = payload.type if payload.type is not None else category.type
    if (name, type_) != (category.name, category.type):
        clash = category_crud.get_by_name_and_type(db, user_id=user_id, name=name, type_=type_)
        if clash is not None and clash.id != category.id:
            raise ConflictError(DUPLICATE_CATEGORY)

    category.name = name
    category.type = type_
    if "color" in changes:  # an explicit null clears the color
        category.color = payload.color

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(DUPLICATE_CATEGORY) from exc
    return category


def delete_category(db: Session, *, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
    """Delete an owned category; its transactions survive uncategorized."""
    category = get_category(db, user_id=user_id, category_id=category_id)
    category_crud.delete(db, category)
