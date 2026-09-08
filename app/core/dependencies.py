from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.auth_user import AuthUser


# ─── Authenticated Dependency (raises 401 if not logged in) ──────────────────


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> AuthUser:
    """
    FastAPI dependency: extracts and validates the logged-in user from a cookie.

    WHAT IS A FASTAPI DEPENDENCY?
    ───────────────────────────────
    A dependency is a function that FastAPI runs automatically before
    executing your route handler. You declare it like this:

        @router.get("/dashboard")
        def dashboard(current_user: AuthUser = Depends(get_current_user)):
            # current_user is already verified and ready to use
            return f"Hello, {current_user.email}"

    FastAPI sees `Depends(get_current_user)` and calls this function first.
    If this function raises an HTTPException, the route never runs.

    HOW IT VALIDATES THE USER (step by step):
    ────────────────────────────────────────────
    1. Read the `access_token` cookie from the HTTP request
    2. If no cookie → 401 Unauthorized
    3. Decode the JWT using our SECRET_KEY
    4. If token is expired or tampered → 401 Unauthorized
    5. Extract the user's ID from the token payload ("sub" field)
    6. Look up that user in the database
    7. If user not found → 401 Unauthorized
    8. If account is deactivated → 403 Forbidden
    9. Return the AuthUser object ✓

    COOKIE VS AUTHORIZATION HEADER:
    ──────────────────────────────────
    We use a cookie (not a Bearer header) because:
    - The browser sends cookies automatically with every request
    - HTTP-only cookies cannot be read by JavaScript (safer)
    - Ideal for server-rendered Jinja2 pages
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Step 1 & 2: Check cookie exists
    if access_token is None:
        raise credentials_exception

    # Step 3 & 4: Decode and verify JWT
    payload = decode_access_token(access_token)
    if payload is None:
        raise credentials_exception

    # Step 5: Extract user ID
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # Step 6: Fetch from database
    statement = select(AuthUser).where(AuthUser.id == user_id)
    result = db.execute(statement)
    user: AuthUser | None = result.scalar_one_or_none()

    # Step 7: User must exist
    if user is None:
        raise credentials_exception

    # Step 8: Account must be active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    # Step 9: Return verified user
    return user


# ─── Optional User Dependency (returns None if not logged in) ─────────────────


def get_optional_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> AuthUser | None:
    """
    Like get_current_user but returns None instead of raising 401.

    WHY DO WE NEED THIS?
    ─────────────────────
    Some pages (Home, About) are visible to everyone — logged in or not.
    But they show DIFFERENT content:
      - Logged in:  "Welcome back, user@email.com" + nav shows Dashboard
      - Not logged in: "Please sign up" + nav shows Login/Register

    We pass the result to templates as `current_user`:
        {% if current_user %}  ← template can check if user is logged in
            <a href="/dashboard">Dashboard</a>
        {% else %}
            <a href="/login">Login</a>
        {% endif %}

    USAGE IN PAGE ROUTES:
    ──────────────────────
        @router.get("/")
        def home_page(
            request: Request,
            current_user: AuthUser | None = Depends(get_optional_user),
        ):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "current_user": current_user,
            })
    """
    if access_token is None:
        return None

    payload = decode_access_token(access_token)
    if payload is None:
        return None

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    statement = select(AuthUser).where(AuthUser.id == user_id)
    result = db.execute(statement)
    user: AuthUser | None = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user
