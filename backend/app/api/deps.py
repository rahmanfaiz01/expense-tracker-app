"""Shared FastAPI dependencies."""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.models import User
from app.models.enums import TransactionType
from app.schemas.transaction import (
    SortOrder,
    TransactionFilters,
    TransactionSort,
)
from app.services.auth import INVALID_TOKEN
from app.services.errors import InvalidRequestError

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
INVALID_DATE_RANGE = "date_from must not be after date_to"

# ``auto_error=False`` so a missing header produces the same generic 401 as a
# bad one instead of FastAPI's default "Not authenticated" body.
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Resolve the bearer access token to an active user.

    Missing, malformed, expired, tampered and non-access tokens, unknown users
    and deactivated accounts are all rejected with the same 401.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized()

    user = user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass(frozen=True)
class Pagination:
    """Validated page number and page size."""

    page: int
    page_size: int


def pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


def transaction_filters(
    q: Annotated[str | None, Query(max_length=255, description="Search in description")] = None,
    type: Annotated[TransactionType | None, Query()] = None,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    sort: Annotated[TransactionSort, Query()] = TransactionSort.OCCURRED_ON,
    order: Annotated[SortOrder, Query()] = SortOrder.DESC,
) -> TransactionFilters:
    """Collect the search/filter/sort query parameters shared by list and export."""
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidRequestError(INVALID_DATE_RANGE)
    return TransactionFilters(
        q=q.strip() if q and q.strip() else None,
        type=type,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        order=order,
    )


Filters = Annotated[TransactionFilters, Depends(transaction_filters)]
PageParams = Annotated[Pagination, Depends(pagination_params)]
