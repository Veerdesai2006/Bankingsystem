from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_user import AuthUser


class AuthRepository:
    """
    Handles all database operations for authentication.

    LAYER RULE: This class ONLY reads/writes the database.
    It never makes business decisions like:
    - "Is this password correct?" (that's AuthService)
    - "Should I reject this request?" (that's AuthService)
    - "What HTTP status code to return?" (that's the API route)

    WHY REPOSITORY PATTERN?
    ──────────────────────────
    If you later switch from PostgreSQL to MySQL (or add a cache layer),
    you only change this file. The service and API layers stay unchanged.
    This is called "Dependency Inversion" — high-level code doesn't depend
    on low-level database details.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> AuthUser | None:
        """
        Find a user by their email address.

        THE BUG THIS FIXES:
        ────────────────────
        The original code ran the query but forgot to return the result:
            result.scalar_one_or_none()   ← result discarded!

        This meant get_by_email always returned None, so the same email
        could register multiple times. The fix is adding `return`.
        """
        statement = select(AuthUser).where(AuthUser.email == email)
        result = self.db.execute(statement)
        return result.scalar_one_or_none()  # ← Bug fix: was missing `return`

    def get_by_id(self, user_id: int) -> AuthUser | None:
        """Find a user by their primary key ID."""
        statement = select(AuthUser).where(AuthUser.id == user_id)
        result = self.db.execute(statement)
        return result.scalar_one_or_none()

    def create_user(self, *, email: str, password_hash: str) -> AuthUser:
        """
        Insert a new user row into the database and return the created object.

        THE * (keyword-only arguments):
        ────────────────────────────────
        The `*` forces callers to use named arguments:
            ✓ create_user(email="a@b.com", password_hash="$argon2...")
            ✗ create_user("a@b.com", "$argon2...")   ← error

        This prevents a subtle bug where someone might accidentally
        swap the email and password_hash arguments.

        db.refresh(user):
        ──────────────────
        After commit(), SQLAlchemy doesn't automatically reload the object
        with database-generated values (like id, created_at, updated_at).
        `refresh()` fetches those values so the returned object is complete.
        """
        user = AuthUser(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user