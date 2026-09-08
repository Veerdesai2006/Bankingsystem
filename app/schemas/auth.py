from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────
#
# WHAT ARE SCHEMAS?
# ─────────────────
# Schemas are Pydantic models. They define what data we EXPECT to receive
# in HTTP requests, and what data we SEND BACK in responses.
#
# Pydantic automatically:
#   1. Validates types:  "abc" is not a valid email → 422 error
#   2. Validates values: password shorter than 8 chars → 422 error
#   3. Converts types:   "true" string → True boolean
#
# Schemas are NOT database models. They are pure Python data containers
# for HTTP input/output validation.
#


class RegisterRequest(BaseModel):
    """Data required to create a new account."""

    email: EmailStr  # Pydantic validates email format automatically
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be 8–128 characters.",
    )


class LoginRequest(BaseModel):
    """Data required to log in."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# ─── Response Schemas ─────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """
    Safe user information to return in API responses.

    CRITICAL SECURITY RULE:
    ────────────────────────
    This schema deliberately EXCLUDES:
      - password_hash  ← NEVER expose this
      - is_superuser   ← internal system field, not for clients

    The `model_config` with `from_attributes=True` allows Pydantic to create
    this object directly from a SQLAlchemy model:
        UserResponse.model_validate(auth_user_object)
    or implicitly via `response_model` in FastAPI routes.
    """

    id: int
    email: str
    is_active: bool
    is_email_verified: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """
    Returned after a successful login.

    The access_token is a JWT that the client stores and sends
    with every subsequent request to prove their identity.

    token_type: "bearer" is the OAuth2 standard naming convention.
    It tells the client "send this token as: Authorization: Bearer <token>"
    (though we also set it as a cookie for Jinja2 pages).
    """

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthResponse(BaseModel):
    """Generic message-only response (e.g., logout confirmation)."""

    message: str