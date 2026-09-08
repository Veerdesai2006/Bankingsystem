import enum
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TransactionType(str, enum.Enum):
    """
    The direction of a banking transaction.

    WHY AN ENUM INSTEAD OF A PLAIN STRING?
    ────────────────────────────────────────
    If we used a plain string, a bug could write "DEPOSITE" or "deposit"
    instead of "DEPOSIT" — different values for the same thing.

    An Enum is a fixed set of allowed values. Anything outside that set
    causes an error immediately. It makes your code self-documenting:
    you know exactly what values are possible.

    `str, enum.Enum` means:
    - The values are strings ("DEPOSIT", "WITHDRAWAL")
    - They serialize to/from JSON automatically
    - They are stored as strings in PostgreSQL
    """

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class Transaction(BaseModel):
    """
    An immutable record of every banking operation.

    THE GOLDEN RULE OF TRANSACTION RECORDS:
    ──────────────────────────────────────────
    Transaction records are NEVER modified or deleted.
    They are a permanent audit trail.

    If a mistake is made → add a REVERSAL transaction (V2 feature)
    Never → edit or delete the original

    This is the foundation of financial integrity and audit compliance.
    In real banking systems, regulators require you to keep transaction
    history for 7–10 years.

    WHAT IS balance_after?
    ───────────────────────
    After each transaction, we store a snapshot of the account balance.
    Example:
        Deposit ₹1000  → balance_after = ₹1000
        Deposit ₹500   → balance_after = ₹1500
        Withdraw ₹200  → balance_after = ₹1300

    This lets you reconstruct the account history without summing everything,
    and makes debugging much easier.

    Table name: transactions
    """

    __tablename__ = "transactions"

    # Link to the bank account this transaction belongs to
    # ondelete="RESTRICT": Prevents deleting an account that has transactions.
    # This protects your audit trail — you cannot accidentally wipe history.
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Was this a DEPOSIT or WITHDRAWAL?
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transactiontype"),
        nullable=False,
    )

    # The amount of this transaction. Always positive.
    # The type (DEPOSIT/WITHDRAWAL) tells you the direction.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )

    # The account balance AFTER this transaction completed.
    # Snapshot for auditing — critical for debugging discrepancies.
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )

    # Optional human-readable note (e.g., "Salary deposit", "ATM withdrawal")
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ─── Relationship ──────────────────────────────────────────────────────
    # Python-side link back to the BankAccount object.
    # Usage: transaction.account → returns the BankAccount object
    account: Mapped["BankAccount"] = relationship(back_populates="transactions")
