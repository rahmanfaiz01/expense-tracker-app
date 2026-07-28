"""Domain errors raised by the service layer.

Endpoints translate these into HTTP responses in one place
(``app.api.deps.http_error``) so every resource reports failures identically.
"""


class ServiceError(Exception):
    """Base class for errors that map onto a client-visible HTTP status."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    """The resource does not exist, or belongs to another user."""


class ConflictError(ServiceError):
    """The request violates a uniqueness rule."""


class InvalidRequestError(ServiceError):
    """The request is syntactically valid but breaks a business rule."""
