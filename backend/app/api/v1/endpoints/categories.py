"""Category CRUD endpoints. Every route is scoped to the authenticated user."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.models.enums import TransactionType
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category as category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: CurrentUser,
    db: DbSession,
    type: Annotated[TransactionType | None, Query()] = None,
) -> list[CategoryRead]:
    """List the current user's categories, optionally filtered by type."""
    categories = category_service.list_categories(db, user_id=current_user.id, type_=type)
    return [CategoryRead.model_validate(category) for category in categories]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    current_user: CurrentUser,
    db: DbSession,
    payload: CategoryCreate,
) -> CategoryRead:
    """Create a category for the current user."""
    category = category_service.create_category(db, user_id=current_user.id, payload=payload)
    db.commit()
    return CategoryRead.model_validate(category)


@router.get("/{category_id}", response_model=CategoryRead)
def read_category(
    current_user: CurrentUser,
    db: DbSession,
    category_id: uuid.UUID,
) -> CategoryRead:
    """Return one of the current user's categories."""
    category = category_service.get_category(db, user_id=current_user.id, category_id=category_id)
    return CategoryRead.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    current_user: CurrentUser,
    db: DbSession,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> CategoryRead:
    """Partially update one of the current user's categories."""
    category = category_service.update_category(
        db, user_id=current_user.id, category_id=category_id, payload=payload
    )
    db.commit()
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    current_user: CurrentUser,
    db: DbSession,
    category_id: uuid.UUID,
) -> Response:
    """Delete a category; its transactions are kept and become uncategorized."""
    category_service.delete_category(db, user_id=current_user.id, category_id=category_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
