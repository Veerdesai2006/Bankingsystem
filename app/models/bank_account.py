from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BankAccount(BaseModel):
    """
    Represents a bank account linked to an AuthUser.

    DESIGN DECISION — WHY SEPARATE FROM AuthUser?
    ───────────────────────────────────────────────
    AuthUser = authentication credentials (how you log in)
    BankAccount = financial account (your money)

    This separation means:
    - A user could have multiple bank accounts (savings, checking) — V2 feature
    - The auth system stays clean and focused

    V1 SIMPLIFICATION:
    ───────────────────
    In V1, each user gets exactly one bank account automatically on first login.
    In V2, we'll add proper customer onboarding and account types.

    THE CRITICAL RULE — NEVER USE FLOAT FOR MONEY:
    ───────────────────────────────────────────────
    Python float example:
        >>> 0.1 + 0.2
        0.30000000000000004   ← WRONG!

    In banking, 1 paisa = 1 paisa, always. No approximations.

    Solution: Python's `Decimal` type + PostgreSQL `NUMERIC` column.
        Decimal("0.1") + Decimal("0.2") == Decimal("0.3")  ← CORRECT ✓

    NUMERIC(precision=15, scale=2) means:
        - Up to 15 total digits
        - Always exactly 2 decimal places
        - Range: up to 9,999,999,999,999.99

    Table name: bank_accounts
    """

    __tablename__ = "bank_accounts"

    # Which auth user owns this account?
    # ForeignKey("auth_users.id") creates a link: bank_accounts.user_id → auth_users.id
    # ondelete="CASCADE": If the user is deleted, their account is deleted too.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # A human-readable unique identifier, like "ACC1234567890"
    account_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Current balance. ALWAYS use Decimal, NEVER float.
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Can this account transact? Inactive accounts are frozen.
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # ─── Relationship ─────────────────────────────────────────────────────────
    # This is a Python-side relationship, NOT a database column.
    # It tells SQLAlchemy: "to get all transactions for this account,
    # look in the Transaction table where account_id == self.id"
    #
    # Usage in Python:
    #   account = db.get(BankAccount, 1)
    #   account.transactions  ← returns list of Transaction objects
    #
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        # cascade: if account is deleted, delete all its transactions too
    )
