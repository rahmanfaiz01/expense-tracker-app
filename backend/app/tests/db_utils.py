"""Helpers for provisioning throwaway PostgreSQL databases in tests."""

import os
from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker_test",
)


def reset_database(url: str) -> None:
    """Drop (if present) and recreate the target database for a clean slate."""
    target = make_url(url)
    db_name = target.database
    assert db_name, "database name is required in the URL"
    maintenance_url = target.set(database="postgres")
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
            conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
    finally:
        engine.dispose()


def drop_database(url: str) -> None:
    """Drop the target database (used for cleanup)."""
    target = make_url(url)
    db_name = target.database
    assert db_name, "database name is required in the URL"
    engine = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    finally:
        engine.dispose()


def make_alembic_config(url: str) -> Config:
    """Build an Alembic ``Config`` pointed at the given database URL."""
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg
