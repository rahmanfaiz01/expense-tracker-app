"""Tests for the Alembic migration: upgrade/downgrade roundtrip and drift."""

from collections.abc import Generator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.tests.db_utils import drop_database, make_alembic_config, reset_database

_MIGRATION_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker_migtest"

_EXPECTED_TABLES = {"users", "categories", "transactions"}


@pytest.fixture()
def fresh_db() -> Generator[str, None, None]:
    reset_database(_MIGRATION_DB_URL)
    yield _MIGRATION_DB_URL
    drop_database(_MIGRATION_DB_URL)


def _table_names(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_upgrade_downgrade_upgrade_roundtrip(fresh_db: str) -> None:
    cfg = make_alembic_config(fresh_db)

    # empty database -> no feature tables
    assert _EXPECTED_TABLES & _table_names(fresh_db) == set()

    command.upgrade(cfg, "head")
    assert _EXPECTED_TABLES <= _table_names(fresh_db)

    command.downgrade(cfg, "base")
    tables_after_down = _table_names(fresh_db)
    assert _EXPECTED_TABLES & tables_after_down == set()

    command.upgrade(cfg, "head")
    assert _EXPECTED_TABLES <= _table_names(fresh_db)


def test_migration_creates_expected_constraints_and_indexes(fresh_db: str) -> None:
    cfg = make_alembic_config(fresh_db)
    command.upgrade(cfg, "head")

    engine = create_engine(fresh_db)
    try:
        insp = inspect(engine)
        txn_indexes = {ix["name"] for ix in insp.get_indexes("transactions")}
        assert "ix_transactions_user_id_occurred_on" in txn_indexes
        assert "ix_transactions_user_id_category_id" in txn_indexes

        check_names = {c["name"] for c in insp.get_check_constraints("transactions")}
        assert "ck_transactions_amount_positive" in check_names
        assert "ck_transactions_currency_format" in check_names

        cat_uniques = {u["name"] for u in insp.get_unique_constraints("categories")}
        assert "uq_categories_user_name_type" in cat_uniques

        # category_id FK on transactions uses SET NULL
        fks = {fk["name"]: fk for fk in insp.get_foreign_keys("transactions")}
        cat_fk = fks["fk_transactions_category_id_categories"]
        assert cat_fk["options"]["ondelete"].upper() == "SET NULL"
        user_fk = fks["fk_transactions_user_id_users"]
        assert user_fk["options"]["ondelete"].upper() == "CASCADE"
    finally:
        engine.dispose()


def test_no_autogenerate_drift(engine: Engine) -> None:
    """Migrated schema must match the ORM metadata (no pending autogen diffs)."""
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        diffs = compare_metadata(ctx, Base.metadata)
    assert diffs == []
