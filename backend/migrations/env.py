"""Alembic migration environment.

The target metadata is taken from ``app.db.base.Base`` after importing all
models so ``alembic revision --autogenerate`` can detect them. The database URL
defaults to application settings but can be overridden by the caller (e.g. tests)
via ``config.set_main_option("sqlalchemy.url", ...)``.
"""

from logging.config import fileConfig

# ``app.models`` import registers all tables on ``Base.metadata``.
import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.db.base import Base
from sqlalchemy import engine_from_config, pool

config = context.config

# Prefer an explicitly provided URL (e.g. from tests); fall back to settings.
_db_url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", _db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection)."""
    context.configure(
        url=_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with a live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
