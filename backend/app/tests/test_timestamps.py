"""Tests for created_at/updated_at behavior across committed transactions."""

import time

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import User
from app.tests.factories import make_user


def test_updated_at_advances_on_update(engine: Engine) -> None:
    """``updated_at`` uses ``func.now()`` (transaction time), so it only changes
    across separate committed transactions; ``created_at`` stays fixed.
    """
    with Session(engine) as session:
        user = make_user()
        session.add(user)
        session.commit()
        user_id = user.id
        created_at = user.created_at
        updated_at_initial = user.updated_at

    try:
        time.sleep(1.1)
        with Session(engine) as session:
            fetched = session.get(User, user_id)
            assert fetched is not None
            fetched.full_name = "Updated Name"
            session.commit()
            assert fetched.created_at == created_at
            assert fetched.updated_at > updated_at_initial
    finally:
        with Session(engine) as session:
            obj = session.get(User, user_id)
            if obj is not None:
                session.delete(obj)
                session.commit()
