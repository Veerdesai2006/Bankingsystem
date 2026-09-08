from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class DepositRequest(BaseModel):
    """
    Data required to make a deposit.

    gt=0 means "greater than 0" — Pydantic rejects 0 or negative amounts.
    decimal_places=2 — rounds to 2 decimal places automatically.
    """

    amount: Decimal = Field(
        gt=Decimal("0"),
        description="Deposit amount. Must be greater than ₹0.00",
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional note (e.g., 'Salary', 'ATM deposit')",
    )


class WithdrawRequest(BaseModel):
    """Data required to make a withdrawal."""

    amount: Decimal = Field(
        gt=Decimal("0"),
        description="Withdrawal amount. Must be greater than ₹0.00",
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional note (e.g., 'Rent payment')",
    )


class BalanceResponse(BaseModel):
    """Account balance information returned to the client."""

    account_number: str
    balance: Decimal

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    """
    Information about a completed transaction.
    Returned after a deposit or withdrawal.
    """

    id: int
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: str | None

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    """Full account details."""

    id: int
    account_number: str
    balance: Decimal
    is_active: bool

    model_config = {"from_attributes": True}
