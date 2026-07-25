"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.models import User
from app.services.auth import INVALID_TOKEN

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
