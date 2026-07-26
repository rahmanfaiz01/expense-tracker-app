"""Transaction business rules: ownership, category consistency, paging."""

import uuid
from collections.abc import Iterator, Sequence
from math import ceil

from sqlalchemy.orm import Session

from app.crud import category as category_crud
from app.crud import transaction as transaction_crud
from app.models import Transaction
from app.models.enums import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionUpdate,
)
from app.services.errors import InvalidRequestError, NotFoundError

TRANSACTION_NOT_FOUND = "Transaction not found"
CATEGORY_NOT_FOUND = "Category not found"
CATEGORY_TYPE_MISMATCH = "Category type does not match the transaction type"


def _validate_category(
    db: Session,
    *,
    user_id: uuid.UUID,
    category_id: uuid.UUID | None,
    type_: TransactionType,
) -> None:
    """Ensure the category is owned by the user and matches the entry type."""
    if category_id is None:
        return
    category = category_crud.get_for_user(db, user_id=user_id, category_id=category_id)
    if category is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    if category.type is not type_:
        raise InvalidRequestError(CATEGORY_TYPE_MISMATCH)


def list_transactions(
    db: Session,
    *,
    user_id: uuid.UUID,
    filters: TransactionFilters,
    page: int,
    page_size: int,
) -> tuple[Sequence[Transaction], int, int]:
    """Return ``(items, total, pages)`` for one page of results."""
    total = transaction_crud.count(db, user_id=user_id, filters=filters)
    items = transaction_crud.list_page(
        db, user_id=user_id, filters=filters, page=page, page_size=page_size
    )
    return items, total, max(1, ceil(total / page_size))


def iter_transactions(
    db: Session,
    *,
    user_id: uuid.UUID,
    filters: TransactionFilters,
) -> Iterator[Transaction]:
    """Stream all matching transactions (no pagination) for the CSV export."""
    return transaction_crud.iter_filtered(db, user_id=user_id, filters=filters)


def get_transaction(db: Session, *, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    """Return one owned transaction, or raise ``NotFoundError``."""
    transaction = transaction_crud.get_for_user(db, user_id=user_id, transaction_id=transaction_id)
    if transaction is None:
        raise NotFoundError(TRANSACTION_NOT_FOUND)
    return transaction


def create_transaction(
    db: Session, *, user_id: uuid.UUID, payload: TransactionCreate
) -> Transaction:
    """Create a transaction after validating its category."""
    _validate_category(db, user_id=user_id, category_id=payload.category_id, type_=payload.type)
    return transaction_crud.create(
        db,
        user_id=user_id,
        type_=payload.type,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        occurred_on=payload.occurred_on,
        category_id=payload.category_id,
    )


def update_transaction(
    db: Session,
    *,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
) -> Transaction:
    """Apply a partial update, re-checking the category against the final type."""
    transaction = get_transaction(db, user_id=user_id, transaction_id=transaction_id)
    changes = payload.model_dump(exclude_unset=True)

    type_ = payload.type if payload.type is not None else transaction.type
    category_id = payload.category_id if "category_id" in changes else transaction.category_id
    _validate_category(db, user_id=user_id, category_id=category_id, type_=type_)

    transaction.type = type_
    transaction.category_id = category_id
    if payload.amount is not None:
        transaction.amount = payload.amount
    if payload.currency is not None:
        transaction.currency = payload.currency
    if payload.occurred_on is not None:
        transaction.occurred_on = payload.occurred_on
    if "description" in changes:  # an explicit null clears the description
        transaction.description = payload.description

    db.flush()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, *, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    """Delete an owned transaction."""
    transaction = get_transaction(db, user_id=user_id, transaction_id=transaction_id)
    transaction_crud.delete(db, transaction)
