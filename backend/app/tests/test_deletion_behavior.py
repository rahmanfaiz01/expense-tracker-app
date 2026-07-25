"""Tests for the documented deletion behavior (cascade / set null)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Transaction
from app.tests.factories import make_category, make_transaction, make_user


def test_deleting_user_cascades_to_categories_and_transactions(db_session: Session) -> None:
    user = make_user()
    category = make_category(user)
    txn = make_transaction(user, category=category)
    db_session.add_all([user, category, txn])
    db_session.flush()

    db_session.delete(user)
    db_session.flush()

    assert db_session.scalar(select(func.count()).select_from(Category)) == 0
    assert db_session.scalar(select(func.count()).select_from(Transaction)) == 0


def test_deleting_category_sets_transaction_category_null(db_session: Session) -> None:
    user = make_user()
    category = make_category(user)
    txn = make_transaction(user, category=category)
    db_session.add_all([user, category, txn])
    db_session.flush()

    db_session.delete(category)
    db_session.flush()
    db_session.refresh(txn)

    # transaction survives, category link cleared
    assert db_session.get(Transaction, txn.id) is not None
    assert txn.category_id is None
    assert db_session.scalar(select(func.count()).select_from(Category)) == 0
