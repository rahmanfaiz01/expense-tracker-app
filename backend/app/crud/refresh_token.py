"""Refresh-token data access.

Tokens are looked up by their SHA-256 digest; raw tokens never reach the
database.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import RefreshToken


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    family_id: uuid.UUID | None = None,
) -> RefreshToken:
    """Store a new refresh token, starting a new family when none is given."""
    token = RefreshToken(
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    db.flush()
    return token


def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    """Return the stored token matching ``token_hash`` or ``None``."""
    return db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()


def revoke(db: Session, token: RefreshToken) -> None:
    """Mark a single token as revoked (idempotent)."""
    if token.revoked_at is None:
        token.revoked_at = datetime.now(timezone.utc)
        db.flush()


def revoke_family(db: Session, family_id: uuid.UUID) -> None:
    """Revoke every live token in a rotation family."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.flush()
