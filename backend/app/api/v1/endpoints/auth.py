"""Authentication endpoints: register, login, refresh, logout."""

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import DbSession
from app.core.config import settings
from app.core.rate_limit import limiter, login_limit, refresh_limit, register_limit
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.auth import AuthError, IssuedTokens, RegistrationError

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, tokens: IssuedTokens) -> None:
    """Attach the rotating refresh token as an HttpOnly cookie.

    The cookie is scoped to the auth path so it is not sent with ordinary API
    calls, and ``max_age`` mirrors the stored token's lifetime.
    """
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=tokens.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh cookie using the same attributes it was set with."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _unauthorized_clearing_cookie(message: str) -> JSONResponse:
    """401 that also drops the refresh cookie.

    Raising ``HTTPException`` would discard the cookie set on the injected
    response, so the failure path returns the response itself.
    """
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": message},
        headers={"WWW-Authenticate": "Bearer"},
    )
    _clear_refresh_cookie(response)
    return response


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(register_limit)
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: DbSession,
) -> AuthResponse:
    """Create an account and log it in immediately."""
    try:
        user, tokens = auth_service.register(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except RegistrationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc

    db.commit()
    _set_refresh_cookie(response, tokens)
    return AuthResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(login_limit)
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: DbSession,
) -> AuthResponse:
    """Exchange email and password for an access token and refresh cookie."""
    try:
        user, tokens = auth_service.login(db, email=payload.email, password=payload.password)
    except AuthError as exc:
        raise _unauthorized(exc.message) from exc

    db.commit()
    _set_refresh_cookie(response, tokens)
    return AuthResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit(refresh_limit)
def refresh(
    request: Request,
    response: Response,
    db: DbSession,
) -> AuthResponse | JSONResponse:
    """Rotate the refresh cookie and return a fresh access token."""
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token:
        return _unauthorized_clearing_cookie(auth_service.INVALID_TOKEN)

    try:
        user, tokens = auth_service.refresh(db, raw_token=raw_token)
    except AuthError as exc:
        db.commit()  # persist family revocation triggered by token reuse
        return _unauthorized_clearing_cookie(exc.message)

    db.commit()
    _set_refresh_cookie(response, tokens)
    return AuthResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: DbSession) -> Response:
    """Revoke the current refresh-token family and clear the cookie."""
    auth_service.logout(db, raw_token=request.cookies.get(settings.REFRESH_COOKIE_NAME))
    db.commit()

    result = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_refresh_cookie(result)
    return result
