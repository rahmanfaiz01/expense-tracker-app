"""Password hashing, JWT access tokens and refresh-token secrets.

Passwords use Argon2id (``argon2-cffi`` defaults). Refresh tokens are opaque
256-bit random strings; only their SHA-256 digest is persisted, so a database
leak does not expose usable tokens. A fast digest is appropriate here (unlike
for passwords) because the token itself is high-entropy and not guessable, and
it lets the database look the token up by an indexed unique column.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError

from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"

_password_hasher = PasswordHasher()

# Verified against when the email is unknown so that login timing does not
# reveal whether an account exists.
_DUMMY_HASH = _password_hasher.hash("dummy-password-for-timing-equalisation")


def hash_password(password: str) -> str:
    """Return an Argon2id hash for ``password``."""
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return ``True`` when ``password`` matches ``hashed_password``."""
    try:
        return _password_hasher.verify(hashed_password, password)
    except (Argon2Error, InvalidHashError):
        return False


def fake_verify_password(password: str) -> None:
    """Burn roughly one hash verification to equalise unknown-email timing."""
    verify_password(password, _DUMMY_HASH)


def needs_rehash(hashed_password: str) -> bool:
    """Return ``True`` when the stored hash uses outdated Argon2 parameters."""
    return _password_hasher.check_needs_rehash(hashed_password)


def create_access_token(subject: uuid.UUID, expires_delta: timedelta | None = None) -> str:
    """Return a signed, short-lived JWT access token for ``subject``."""
    now = datetime.now(timezone.utc)
    expires = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, str | int] = {
        "sub": str(subject),
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID | None:
    """Return the subject of a valid access token, or ``None`` if unusable.

    Expired, tampered, wrongly-typed and malformed tokens are all rejected the
    same way so callers cannot distinguish between the failure modes.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        return None
    try:
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        return None


def generate_refresh_token() -> str:
    """Return a new opaque refresh-token secret (URL-safe, 256 bits)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Return the SHA-256 digest stored in place of a raw refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
