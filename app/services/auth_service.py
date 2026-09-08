from app.core.security import hash_password, verify_password
from app.models.auth_user import AuthUser
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.core.security import create_access_token


class AuthService:
    """
    All authentication business logic lives here.

    LAYER RULES:
    ─────────────
    ✓ Can call AuthRepository to read/write the database
    ✓ Can make business decisions ("Is this email taken?")
    ✓ Can call security utilities (hash_password, create_access_token)
    ✗ Cannot touch HTTP directly (no Request, no Response, no status codes)
    ✗ Cannot call the API layer

    WHY SEPARATE SERVICE + REPOSITORY?
    ────────────────────────────────────
    If you change the database (PostgreSQL → MySQL), only the Repository changes.
    If you change the business rules ("passwords must be 12 chars now"), only
    the Service changes. Neither affects the other. This is "separation of concerns."
    """

    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def register_user(self, request: RegisterRequest) -> AuthUser:
        """
        Register a new portal user.

        FLOW:
        ──────
        1. Check if email already exists → raise error if so
        2. Hash the password (NEVER store plain text)
        3. Create user in database
        4. Return the AuthUser object

        WHY NOT return TokenResponse (auto-login after register)?
        ───────────────────────────────────────────────────────────
        V1 design: register → redirect to login.
        This is simpler and avoids edge cases with unverified emails.
        """
        # Step 1: Duplicate email check
        existing_user = self.repository.get_by_email(request.email)
        if existing_user:
            raise ValueError("An account with this email already exists.")

        # Step 2: Hash password
        hashed = hash_password(request.password)

        # Step 3 & 4: Create and return
        return self.repository.create_user(
            email=request.email,
            password_hash=hashed,
        )

    def login_user(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and return a JWT access token.

        SECURITY DESIGN — GENERIC ERROR MESSAGES:
        ───────────────────────────────────────────
        We return the SAME error for both "email not found" and
        "wrong password": "Invalid email or password."

        WHY?
        If we said "email not found," an attacker could write a script
        that tries thousands of emails to discover which ones are
        registered in our system. This is called "user enumeration."

        By giving the same message for both cases, we reveal nothing.

        FLOW:
        ──────
        1. Look up user by email
        2. If not found → generic "Invalid email or password" error
        3. Verify password against stored hash
        4. If wrong → same generic error
        5. Check account is active
        6. Create JWT (user's ID as the subject)
        7. Return token + user info
        """
        # Steps 1 & 2
        user = self.repository.get_by_email(request.email)
        if user is None:
            raise ValueError("Invalid email or password.")

        # Step 3 & 4
        if not verify_password(request.password, user.password_hash):
            raise ValueError("Invalid email or password.")

        # Step 5: Inactive accounts get a different, specific error
        # (the user knows their account exists but is suspended)
        if not user.is_active:
            raise ValueError(
                "Your account has been deactivated. Please contact support."
            )

        # Step 6: Create JWT with user's ID as subject
        token = create_access_token(subject=user.id)

        # Step 7: Return full token response
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
            ),
        )
