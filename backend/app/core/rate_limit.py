"""Rate limiting for authentication endpoints.

Limits are keyed by client IP and held in process memory, which is enough for
the single-instance Railway deployment; moving to Redis only requires passing a
``storage_uri`` here.
"""

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

TOO_MANY_REQUESTS = "Too many requests, please try again later"

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Return a generic 429 with ``Retry-After`` for throttled requests."""
    headers = {}
    if isinstance(exc, RateLimitExceeded) and exc.limit is not None:
        headers["Retry-After"] = str(exc.limit.limit.GRANULARITY.seconds)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": TOO_MANY_REQUESTS},
        headers=headers,
    )


def register_limit() -> str:
    """Return the configured registration limit (read per request)."""
    return settings.RATE_LIMIT_REGISTER


def login_limit() -> str:
    """Return the configured login limit (read per request)."""
    return settings.RATE_LIMIT_LOGIN


def refresh_limit() -> str:
    """Return the configured refresh limit (read per request)."""
    return settings.RATE_LIMIT_REFRESH
