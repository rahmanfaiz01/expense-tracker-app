"""SQLAlchemy declarative base.

Feature models (users, categories, transactions) will subclass ``Base`` in
later phases. Keeping the base isolated lets Alembic autogenerate migrations by
importing a single metadata object.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
