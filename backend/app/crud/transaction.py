"""Transaction data access. Every query is scoped to the owning user."""

import uuid
from collections.abc import Iterator, Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Transaction
from app.models.enums import TransactionType
from app.schemas.transaction import SortOrder, TransactionFilters, TransactionSort

_SORT_COLUMNS = {
    TransactionSort.OCCURRED_ON: Transaction.occurred_on,
    TransactionSort.AMOUNT: Transaction.amount,
    TransactionSort.CREATED_AT: Transaction.created_at,
    TransactionSort.DESCRIPTION: Transaction.description,
}

_STREAM_BATCH_SIZE = 500


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so a literal ``%`` or ``_`` is matched as typed."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def filtered_query(user_id: uuid.UUID, filters: TransactionFilters) -> Select[tuple[Transaction]]:
    """Build the base SELECT shared by listing, counting and CSV export."""
    stmt = select(Transaction).where(Transaction.user_id == user_id)

    if filters.q:
        pattern = f"%{_escape_like(filters.q)}%"
        stmt = stmt.where(Transaction.description.ilike(pattern, escape="\\"))
    if filters.type is not None:
        stmt = stmt.where(Transaction.type == filters.type)
    if filters.category_id is not None:
        stmt = stmt.where(Transaction.category_id == filters.category_id)
    if filters.date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= filters.date_to)
    return stmt


def _sorted(
    stmt: Select[tuple[Transaction]], filters: TransactionFilters
) -> Select[tuple[Transaction]]:
    column = _SORT_COLUMNS[filters.sort]
    ordering = column.asc() if filters.order is SortOrder.ASC else column.desc()
    # ``id`` breaks ties so pagination is stable when the sort key repeats.
    return stmt.order_by(ordering.nullslast(), Transaction.id)


def count(db: Session, *, user_id: uuid.UUID, filters: TransactionFilters) -> int:
    """Count the transactions matching ``filters``."""
    stmt = filtered_query(user_id, filters).with_only_columns(func.count()).order_by(None)
    return db.execute(stmt).scalar_one()


def list_page(
    db: Session,
    *,
    user_id: uuid.UUID,
    filters: TransactionFilters,
    page: int,
    page_size: int,
) -> Sequence[Transaction]:
    """Return one page of matching transactions with their categories loaded."""
    stmt = (
        _sorted(filtered_query(user_id, filters), filters)
        .options(joinedload(Transaction.category))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return db.execute(stmt).scalars().all()


def iter_filtered(
    db: Session,
    *,
    user_id: uuid.UUID,
    filters: TransactionFilters,
) -> Iterator[Transaction]:
    """Stream every matching transaction in batches (used by the CSV export)."""
    stmt = _sorted(filtered_query(user_id, filters), filters).options(
        joinedload(Transaction.category)
    )
    yield from db.execute(stmt).unique().scalars().yield_per(_STREAM_BATCH_SIZE)


def get_for_user(
    db: Session, *, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction | None:
    """Return one transaction owned by ``user_id`` or ``None``."""
    return db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    ).scalar_one_or_none()


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: TransactionType,
    amount: Decimal,
    currency: str,
    description: str | None,
    occurred_on: date,
    category_id: uuid.UUID | None,
) -> Transaction:
    """Insert a transaction and flush so the generated id is available."""
    transaction = Transaction(
        user_id=user_id,
        type=type_,
        amount=amount,
        currency=currency,
        description=description,
        occurred_on=occurred_on,
        category_id=category_id,
    )
    db.add(transaction)
    db.flush()
    return transaction


def delete(db: Session, transaction: Transaction) -> None:
    """Delete a single transaction."""
    db.delete(transaction)
    db.flush()
