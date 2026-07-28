"""Configuration guardrails."""

import pytest
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET_KEY, Settings


def test_production_rejects_the_development_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY=DEV_JWT_SECRET_KEY)


def test_production_rejects_a_short_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="too-short")


def test_production_accepts_an_explicit_secret() -> None:
    secret = "a-real-secret-from-the-vault-32-chars-plus"
    settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY=secret)

    assert settings.JWT_SECRET_KEY == secret


def test_cross_site_cookie_configuration_is_supported() -> None:
    settings = Settings(COOKIE_SECURE=True, COOKIE_SAMESITE="none")

    assert settings.COOKIE_SECURE is True
    assert settings.COOKIE_SAMESITE == "none"


def test_same_site_none_requires_a_secure_cookie() -> None:
    with pytest.raises(ValidationError):
        Settings(COOKIE_SECURE=False, COOKIE_SAMESITE="none")


@pytest.mark.parametrize(
    "url",
    [
        "postgres://user:pw@host:5432/railway",
        "postgresql://user:pw@host:5432/railway",
    ],
)
def test_managed_database_urls_get_the_psycopg_driver(url: str) -> None:
    settings = Settings(DATABASE_URL=url)

    assert settings.DATABASE_URL == "postgresql+psycopg://user:pw@host:5432/railway"


def test_an_explicit_driver_is_left_alone() -> None:
    url = "postgresql+psycopg://user:pw@host:5432/railway"

    assert Settings(DATABASE_URL=url).DATABASE_URL == url


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:5173, https://app.vercel.app")

    assert settings.cors_origins == ["http://localhost:5173", "https://app.vercel.app"]
