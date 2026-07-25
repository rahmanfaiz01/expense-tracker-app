"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET_KEY = "dev-only-insecure-secret-change-me"


class Settings(BaseSettings):
    """Central application settings.

    Values are read from environment variables (or a local ``.env`` file in
    development). See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    PROJECT_NAME: str = "Expense Tracker API"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker",
        description="SQLAlchemy database URL.",
    )

    # CORS: comma-separated list of allowed origins.
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    # Authentication. JWT_SECRET_KEY MUST be overridden outside development;
    # rotating it invalidates every issued access token.
    JWT_SECRET_KEY: str = DEV_JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Refresh-token cookie. Defaults suit local http development; for
    # Vercel -> Railway (cross-site) use COOKIE_SECURE=true and COOKIE_SAMESITE=none.
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str | None = None

    # Rate limiting (slowapi syntax, e.g. "10/minute").
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured CORS origins as a list."""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _require_production_secret(self) -> "Settings":
        """Refuse to boot a production deployment with the development secret."""
        if self.ENVIRONMENT == "production" and self.JWT_SECRET_KEY == DEV_JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set to a strong secret in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()


settings = get_settings()
