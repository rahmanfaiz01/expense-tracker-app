"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.common import normalize_email
from app.schemas.user import UserCreate, UserRead


class RegisterRequest(UserCreate):
    """Registration payload: validated email, policy-checked password."""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class TokenResponse(BaseModel):
    """Access token returned in the body; the refresh token is cookie-only."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    """Token plus the authenticated user, returned by register and login."""

    user: UserRead
