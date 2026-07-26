"""Dashboard summary and report endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import INVALID_DATE_RANGE, CurrentUser, DbSession
from app.models.enums import TransactionType
from app.schemas.report import CategoryTotal, MonthlyPoint, SummaryRead
from app.services import report as report_service
from app.services.errors import InvalidRequestError

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_MONTHS = 36
DEFAULT_MONTHS = 6


def _check_range(date_from: date | None, date_to: date | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidRequestError(INVALID_DATE_RANGE)


@router.get("/summary", response_model=SummaryRead)
def read_summary(
    current_user: CurrentUser,
    db: DbSession,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> SummaryRead:
    """Total income, total expenses and balance for the period."""
    _check_range(date_from, date_to)
    return report_service.summary(db, user_id=current_user.id, date_from=date_from, date_to=date_to)


@router.get("/monthly", response_model=list[MonthlyPoint])
def read_monthly(
    current_user: CurrentUser,
    db: DbSession,
    months: Annotated[int, Query(ge=1, le=MAX_MONTHS)] = DEFAULT_MONTHS,
) -> list[MonthlyPoint]:
    """Income and expenses per month for the last ``months`` months."""
    return report_service.monthly(db, user_id=current_user.id, months=months)


@router.get("/by-category", response_model=list[CategoryTotal])
def read_by_category(
    current_user: CurrentUser,
    db: DbSession,
    type: Annotated[TransactionType, Query()] = TransactionType.EXPENSE,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> list[CategoryTotal]:
    """Totals grouped by category for the period (expenses by default)."""
    _check_range(date_from, date_to)
    return report_service.by_category(
        db, user_id=current_user.id, type_=type, date_from=date_from, date_to=date_to
    )
