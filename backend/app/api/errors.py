"""Translation of service-layer errors into HTTP responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.services.errors import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    ServiceError,
)

_STATUS_BY_ERROR: dict[type[ServiceError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidRequestError: status.HTTP_400_BAD_REQUEST,
}


def service_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return ``{"detail": ...}`` with the status mapped from the error type.

    Keeping the mapping here means every resource reports the same shape as the
    auth endpoints and FastAPI's own ``HTTPException`` responses.
    """
    if not isinstance(exc, ServiceError):  # pragma: no cover - defensive
        raise exc
    status_code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": exc.message})
