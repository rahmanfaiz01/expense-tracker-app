"""User data access."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Return the user with ``user_id`` or ``None``."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Return the user with ``email`` (already normalized) or ``None``."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def create(db: Session, *, email: str, hashed_password: str, full_name: str | None) -> User:
    """Insert a new user and flush so the generated id is available."""
    user = User(email=email, hashed_password=hashed_password, full_name=full_name)
    db.add(user)
    db.flush()
    return user
