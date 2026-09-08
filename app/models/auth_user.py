from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuthUser(BaseModel):
    """
    Stores authentication credentials for every registered user.

    DESIGN DECISION — Why a separate auth table?
    ─────────────────────────────────────────────
    This table ONLY stores how a user logs in:
      - Their email (login identifier)
      - Their hashed password
      - Their account status flags
      - Their role (admin or regular)

    It does NOT store:
      - Full name, address, phone (that goes in a Customer profile later)
      - Bank account number, balance (that goes in BankAccount model)

    This separation is called "Single Responsibility Principle."
    Each table does ONE thing well. When you later add OAuth login
    or multi-factor authentication, you only touch this table.

    COLUMNS INHERITED FROM BaseModel:
      - id         (primary key, auto-increment)
      - created_at (timestamp of registration)
      - updated_at (timestamp of last profile change)

    Table name: auth_users
    """

    __tablename__ = "auth_users"

    # The user's login email. Must be unique across all accounts.
    # index=True creates a fast lookup index (email is queried on every login).
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # We NEVER store the plain password. Only the Argon2 hash.
    # The hash is ~97 characters long, so String(255) is safe.
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Can this user log in? Setting this to False deactivates an account
    # without deleting it (useful for suspending users).
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Has the user verified their email address?
    # In V1, this is always False (we don't send verification emails yet).
    # We track it now so we can enforce it later without a migration.
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Is this user an administrator (superuser)?
    # Regular users: False. Bank admin staff: True.
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )