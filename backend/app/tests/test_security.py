"""Unit tests for password hashing, JWT handling and refresh-token secrets."""

import uuid
from datetime import timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.schemas.common import validate_password


def test_password_hash_is_argon2id_and_salted() -> None:
    first = security.hash_password("correct-horse-9")
    second = security.hash_password("correct-horse-9")

    assert first.startswith("$argon2id$")
    assert first != second
    assert "correct-horse-9" not in first


def test_verify_password_accepts_correct_and_rejects_wrong() -> None:
    hashed = security.hash_password("correct-horse-9")

    assert security.verify_password("correct-horse-9", hashed)
    assert not security.verify_password("Correct-horse-9", hashed)
    assert not security.verify_password("", hashed)


def test_verify_password_rejects_garbage_hash() -> None:
    assert not security.verify_password("correct-horse-9", "not-a-hash")


def test_access_token_round_trip() -> None:
    subject = uuid.uuid4()

    token = security.create_access_token(subject)

    assert security.decode_access_token(token) == subject


def test_access_token_carries_expected_claims() -> None:
    token = security.create_access_token(uuid.uuid4())

    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert payload["jti"]


def test_expired_access_token_is_rejected() -> None:
    token = security.create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=-1))

    assert security.decode_access_token(token) is None


def test_token_signed_with_another_key_is_rejected() -> None:
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access", "exp": 9999999999},
        "a-different-signing-key-of-sufficient-length",
        algorithm="HS256",
    )

    assert security.decode_access_token(token) is None


def test_unsigned_and_wrongly_typed_tokens_are_rejected() -> None:
    unsigned = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "access", "exp": 9999999999},
        key="",
        algorithm="none",
    )
    wrong_type = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "refresh", "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert security.decode_access_token(unsigned) is None
    assert security.decode_access_token(wrong_type) is None
    assert security.decode_access_token("garbage") is None


def test_refresh_tokens_are_unique_and_hashed_deterministically() -> None:
    first = security.generate_refresh_token()
    second = security.generate_refresh_token()

    assert first != second
    assert len(first) >= 43  # 256 bits, url-safe base64
    assert security.hash_refresh_token(first) == security.hash_refresh_token(first)
    assert security.hash_refresh_token(first) != security.hash_refresh_token(second)
    assert len(security.hash_refresh_token(first)) == 64


@pytest.mark.parametrize(
    "password",
    ["short1a", "no-digits-here", "1234567890", "a1" * 100],
)
def test_password_policy_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(ValueError):
        validate_password(password)


def test_password_policy_accepts_reasonable_password() -> None:
    assert validate_password("correct-horse-9") == "correct-horse-9"
