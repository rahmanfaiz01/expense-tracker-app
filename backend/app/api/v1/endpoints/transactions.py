"""Transaction CRUD, filtered listing and CSV export."""

import csv
import io
import uuid
from collections.abc import Iterable
from datetime import date

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession, Filters, PageParams
from app.models import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction as transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])

CSV_HEADER = ["date", "type", "category", "description", "amount", "currency"]
CSV_FILENAME = "transactions.csv"


@router.get("", response_model=TransactionPage)
def list_transactions(
    current_user: CurrentUser,
    db: DbSession,
    filters: Filters,
    pagination: PageParams,
) -> TransactionPage:
    """List the current user's transactions with search, filters and paging."""
    items, total, pages = transaction_service.list_transactions(
        db,
        user_id=current_user.id,
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return TransactionPage(
        items=[TransactionRead.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )


def _render_csv(transactions: Iterable[Transaction]) -> str:
    """Render matching transactions as CSV text.

    Rows are pulled from the database in batches, but the body is built eagerly:
    a streaming response would outlive the request-scoped session.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    for transaction in transactions:
        writer.writerow(
            [
                transaction.occurred_on.isoformat(),
                transaction.type.value,
                transaction.category_name or "",
                transaction.description or "",
                f"{transaction.amount:.2f}",
                transaction.currency,
            ]
        )
    return buffer.getvalue()


@router.get(
    "/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}, "description": "CSV export"}},
)
def export_transactions_csv(
    current_user: CurrentUser,
    db: DbSession,
    filters: Filters,
) -> Response:
    """Export every transaction matching the active filters as CSV."""
    body = _render_csv(
        transaction_service.iter_transactions(db, user_id=current_user.id, filters=filters)
    )
    filename = _export_filename(filters)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _export_filename(filters: TransactionFilters) -> str:
    """Name the download after the filtered period when one is set."""
    if filters.date_from is None and filters.date_to is None:
        return CSV_FILENAME
    start = (filters.date_from or date.min).isoformat()
    end = (filters.date_to or date.today()).isoformat()
    return f"transactions_{start}_{end}.csv"


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    current_user: CurrentUser,
    db: DbSession,
    payload: TransactionCreate,
) -> TransactionRead:
    """Create an income or expense entry for the current user."""
    transaction = transaction_service.create_transaction(
        db, user_id=current_user.id, payload=payload
    )
    db.commit()
    return TransactionRead.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionRead)
def read_transaction(
    current_user: CurrentUser,
    db: DbSession,
    transaction_id: uuid.UUID,
) -> TransactionRead:
    """Return one of the current user's transactions."""
    transaction = transaction_service.get_transaction(
        db, user_id=current_user.id, transaction_id=transaction_id
    )
    return TransactionRead.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    current_user: CurrentUser,
    db: DbSession,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
) -> TransactionRead:
    """Partially update one of the current user's transactions."""
    transaction = transaction_service.update_transaction(
        db, user_id=current_user.id, transaction_id=transaction_id, payload=payload
    )
    db.commit()
    return TransactionRead.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    current_user: CurrentUser,
    db: DbSession,
    transaction_id: uuid.UUID,
) -> Response:
    """Delete one of the current user's transactions."""
    transaction_service.delete_transaction(
        db, user_id=current_user.id, transaction_id=transaction_id
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
