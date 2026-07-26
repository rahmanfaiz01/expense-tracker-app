"""Authentication use-cases: registration, login, rotation and revocation.

The service raises :class:`AuthError` for every failure the caller is allowed to
see. Messages are deliberately coarse so responses cannot be used to probe which
accounts exist or why a token was refused.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.crud import refresh_token as refresh_token_crud
from app.crud import user as user_crud
from app.models import RefreshToken, User

INVALID_CREDENTIALS = "Invalid email or password"
INVALID_TOKEN = "Invalid or expired credentials"
REGISTRATION_FAILED = "Registration could not be completed"


class AuthError(Exception):
    """Raised when a request must be rejected; carries a client-safe message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RegistrationError(AuthError):
    """Raised when an account cannot be created (e.g. the email is taken)."""


@dataclass(frozen=True)
class IssuedTokens:
    """An access token plus the raw refresh token to place in the cookie."""

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_at: datetime


def _issue_tokens(db: Session, user: User, *, family_id: uuid.UUID | None = None) -> IssuedTokens:
    """Mint an access token and persist a hashed refresh token for ``user``."""
    raw_refresh = security.generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_crud.create(
        db,
        user_id=user.id,
        token_hash=security.hash_refresh_token(raw_refresh),
        expires_at=expires_at,
        family_id=family_id,
    )
    return IssuedTokens(
        access_token=security.create_access_token(user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=raw_refresh,
        refresh_expires_at=expires_at,
    )


def register(
    db: Session, *, email: str, password: str, full_name: str | None
) -> tuple[User, IssuedTokens]:
    """Create an account and log it in.

    Raises :class:`RegistrationError` when the email is already registered. The
    unique index is the source of truth, so a concurrent duplicate is caught as
    an ``IntegrityError`` rather than winning a race against a pre-check.
    """
    if user_crud.get_by_email(db, email) is not None:
        raise RegistrationError(REGISTRATION_FAILED)

    try:
        user = user_crud.create(
            db,
            email=email,
            hashed_password=security.hash_password(password),
            full_name=full_name,
        )
    except IntegrityError as exc:
        db.rollback()
        raise RegistrationError(REGISTRATION_FAILED) from exc

    return user, _issue_tokens(db, user)


def login(db: Session, *, email: str, password: str) -> tuple[User, IssuedTokens]:
    """Authenticate a user and issue a new token pair.

    Unknown emails, wrong passwords and deactivated accounts all raise the same
    :class:`AuthError`; unknown emails still pay for a hash verification so the
    response time does not leak account existence.
    """
    user = user_crud.get_by_email(db, email)
    if user is None:
        security.fake_verify_password(password)
        raise AuthError(INVALID_CREDENTIALS)
    if not security.verify_password(password, user.hashed_password):
        raise AuthError(INVALID_CREDENTIALS)
    if not user.is_active:
        raise AuthError(INVALID_CREDENTIALS)

    if security.needs_rehash(user.hashed_password):
        user.hashed_password = security.hash_password(password)
        db.flush()

    return user, _issue_tokens(db, user)


def _load_live_token(db: Session, raw_token: str) -> RefreshToken:
    """Return a usable stored token, revoking the family on replay.

    Presenting an already-revoked token means either the legitimate client
    replayed it or a stolen copy is in use; either way the whole rotation family
    is revoked so the thief and the victim are both logged out.
    """
    stored = refresh_token_crud.get_by_hash(db, security.hash_refresh_token(raw_token))
    if stored is None:
        raise AuthError(INVALID_TOKEN)
    if stored.revoked_at is not None:
        refresh_token_crud.revoke_family(db, stored.family_id)
        raise AuthError(INVALID_TOKEN)
    if stored.expires_at <= datetime.now(timezone.utc):
        refresh_token_crud.revoke(db, stored)
        raise AuthError(INVALID_TOKEN)
    return stored


def refresh(db: Session, *, raw_token: str) -> tuple[User, IssuedTokens]:
    """Rotate a refresh token: revoke the presented one, issue its successor."""
    stored = _load_live_token(db, raw_token)

    user = user_crud.get_by_id(db, stored.user_id)
    if user is None or not user.is_active:
        refresh_token_crud.revoke_family(db, stored.family_id)
        raise AuthError(INVALID_TOKEN)

    refresh_token_crud.revoke(db, stored)
    return user, _issue_tokens(db, user, family_id=stored.family_id)


def logout(db: Session, *, raw_token: str | None) -> None:
    """Revoke the presented token's family. Unknown tokens are ignored.

    Logout is idempotent and never reports failure: a client that has lost its
    cookie should still be able to clear local state.
    """
    if not raw_token:
        return
    stored = refresh_token_crud.get_by_hash(db, security.hash_refresh_token(raw_token))
    if stored is not None:
        refresh_token_crud.revoke_family(db, stored.family_id)
