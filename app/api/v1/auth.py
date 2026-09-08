from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create a new portal user account.

    WHAT THIS ENDPOINT DOES:
    ─────────────────────────
    1. Pydantic validates email format and password length (automatic)
    2. AuthService checks for duplicate email
    3. Password is hashed with Argon2
    4. User is saved to the database
    5. Returns safe user info (no password hash in response)

    WHAT IT DOES NOT DO (by design):
    ──────────────────────────────────
    - It does NOT log you in automatically (you must call /login after)
    - It does NOT send a verification email (V2 feature)

    HTTP 201 Created = "a new resource was successfully created"
    """
    repository = AuthRepository(db)
    service = AuthService(repository)

    try:
        user = service.register_user(request)
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive a JWT access token",
)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate and receive a JWT access token.

    TOKEN DELIVERY — TWO WAYS:
    ───────────────────────────
    1. JSON response body:
       → Used when testing via Swagger UI or API tools
       → The token appears in the JSON you see on screen

    2. HTTP-only cookie:
       → Used automatically by the browser for Jinja2 pages
       → JavaScript CANNOT read HTTP-only cookies (XSS protection)
       → Browser sends it automatically with every page request
       → This is why you stay "logged in" as you navigate pages

    WHY HTTP 401 (not 400)?
    ─────────────────────────
    HTTP 400 = "bad request" (malformed data)
    HTTP 401 = "unauthorized" (identity check failed)
    Login failures are identity failures → 401 is correct.
    """
    repository = AuthRepository(db)
    service = AuthService(repository)

    try:
        token_data = service.login_user(request)

        # Set the JWT as an HTTP-only cookie for the web frontend
        response.set_cookie(
            key="access_token",
            value=token_data.access_token,
            httponly=True,    # JavaScript cannot access this cookie (XSS protection)
            max_age=settings.access_token_expire_minutes * 60,  # seconds
            samesite="lax",   # Prevents CSRF attacks on cross-site navigation
            secure=settings.app_env == "production",  # HTTPS-only in production
            path="/",         # Cookie is sent for all paths
        )

        return token_data

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and clear the session cookie",
)
def logout(response: Response) -> AuthResponse:
    """
    Log out the current user by deleting the access_token cookie.

    HOW LOGOUT WORKS:
    ──────────────────
    We tell the browser to delete its `access_token` cookie.
    The browser removes the cookie, so it's no longer sent with requests.
    From that point, the user is treated as unauthenticated.

    NOTE ON JWT VALIDITY:
    ─────────────────────
    The JWT token itself is still technically valid until its expiry time
    (30 minutes by default). We just delete it from the cookie so the
    browser never sends it again.

    In V2, we'll add a token blacklist in Redis to immediately invalidate
    the token on the server side. For V1, cookie deletion is sufficient.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
    )
    return AuthResponse(message="Successfully logged out. Goodbye!")