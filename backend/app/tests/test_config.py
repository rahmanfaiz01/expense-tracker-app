"""Configuration guardrails."""

import pytest
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET_KEY, Settings


def test_production_rejects_the_development_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY=DEV_JWT_SECRET_KEY)


def test_production_accepts_an_explicit_secret() -> None:
    settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="a-real-secret-from-the-vault")

    assert settings.JWT_SECRET_KEY == "a-real-secret-from-the-vault"


def test_cross_site_cookie_configuration_is_supported() -> None:
    settings = Settings(COOKIE_SECURE=True, COOKIE_SAMESITE="none")

    assert settings.COOKIE_SECURE is True
    assert settings.COOKIE_SAMESITE == "none"


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:5173, https://app.vercel.app")

    assert settings.cors_origins == ["http://localhost:5173", "https://app.vercel.app"]
