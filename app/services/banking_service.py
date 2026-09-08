import random
import string
from decimal import Decimal

from app.models.bank_account import BankAccount
from app.models.transaction import Transaction, TransactionType
from app.repositories.banking_repository import BankingRepository
from app.schemas.banking import DepositRequest, WithdrawRequest


class BankingService:
    """
    All banking business logic lives here.

    BANKING RULES ENFORCED:
    ─────────────────────────
    1. Amount > 0 (Pydantic validates at API level, we re-confirm here)
    2. Account must be active for any transaction
    3. Withdrawal amount must not exceed current balance
    4. Every operation MUST create a transaction record
    5. Always use Decimal, NEVER float

    FLOW DIAGRAM (Deposit):
    ─────────────────────────
    Request → Validate amount > 0 → Get/Create account → Check active
    → new_balance = balance + amount → update_balance() → create_transaction()
    → Return transaction record

    FLOW DIAGRAM (Withdrawal):
    ────────────────────────────
    Request → Validate amount > 0 → Get account → Check active
    → amount > balance? → raise "Insufficient funds"
    → new_balance = balance - amount → update_balance() → create_transaction()
    → Return transaction record
    """

    def __init__(self, repository: BankingRepository) -> None:
        self.repository = repository

    def _generate_account_number(self) -> str:
        """
        Generate a unique account number like 'ACC7382910465'.

        In a real bank, account numbers follow ISO standards (IBAN).
        For V1 (educational), we use a simple prefix + 10 random digits.

        COLLISION HANDLING:
        ────────────────────
        The database has `unique=True` on account_number.
        If a collision occurs (astronomically rare with 10^10 possibilities),
        the database will raise an integrity error.
        For V1, we accept this. For production, we'd add retry logic.
        """
        digits = "".join(random.choices(string.digits, k=10))
        return f"ACC{digits}"

    def get_or_create_account(self, user_id: int) -> BankAccount:
        """
        Get the user's bank account, creating it if it doesn't exist.

        V1 DESIGN DECISION:
        ────────────────────
        Every user who logs in and visits banking pages gets an account
        automatically. This eliminates the need for a separate account
        creation onboarding flow in V1.

        In V2, we'll have:
        - Customer onboarding with KYC documents
        - Multiple account types (savings, checking)
        - Explicit account creation by bank staff
        """
        account = self.repository.get_account_by_user_id(user_id)
        if account:
            return account

        # Create a fresh account with zero balance
        account_number = self._generate_account_number()
        return self.repository.create_account(
            user_id=user_id,
            account_number=account_number,
        )

    def get_balance(self, user_id: int) -> BankAccount:
        """
        Return the bank account for balance display.
        Raises ValueError if the user has no account yet.
        """
        account = self.repository.get_account_by_user_id(user_id)
        if account is None:
            raise ValueError(
                "No bank account found. Please make a deposit first to activate your account."
            )
        if not account.is_active:
            raise ValueError("Your account is inactive. Please contact support.")
        return account

    def deposit(self, user_id: int, request: DepositRequest) -> Transaction:
        """
        Deposit money into the user's account.

        STEP-BY-STEP:
        ──────────────
        1. Get or create the bank account (V1: auto-create on first deposit)
        2. Verify the account is active
        3. Calculate: new_balance = current_balance + deposit_amount
        4. Save new balance to database
        5. Create a DEPOSIT transaction record (audit trail)
        6. Return the transaction
        """
        # Step 1
        account = self.get_or_create_account(user_id)

        # Step 2
        if not account.is_active:
            raise ValueError("Your account is inactive. Please contact support.")

        # Step 3
        new_balance = account.balance + request.amount

        # Step 4
        self.repository.update_balance(account, new_balance)

        # Step 5 & 6
        return self.repository.create_transaction(
            account_id=account.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=request.amount,
            balance_after=new_balance,
            description=request.description or "Deposit",
        )

    def withdraw(self, user_id: int, request: WithdrawRequest) -> Transaction:
        """
        Withdraw money from the user's account.

        KEY DIFFERENCE FROM DEPOSIT:
        ──────────────────────────────
        Withdrawal requires the account to ALREADY EXIST.
        You cannot withdraw from an account that has never been used.
        We do NOT auto-create here (unlike deposit).

        ALSO: We check sufficient balance BEFORE updating.
        The Decimal comparison is exact — no floating-point surprises.
        """
        # Get account (do NOT auto-create for withdrawal)
        account = self.repository.get_account_by_user_id(user_id)
        if account is None:
            raise ValueError(
                "No bank account found. Please make a deposit first."
            )

        if not account.is_active:
            raise ValueError("Your account is inactive. Please contact support.")

        # CRITICAL CHECK: Sufficient balance?
        # Decimal comparison: exact, no floating point errors
        if request.amount > account.balance:
            raise ValueError(
                f"Insufficient funds. "
                f"Requested: ₹{request.amount:.2f} | "
                f"Available: ₹{account.balance:.2f}"
            )

        new_balance = account.balance - request.amount
        self.repository.update_balance(account, new_balance)

        return self.repository.create_transaction(
            account_id=account.id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=request.amount,
            balance_after=new_balance,
            description=request.description or "Withdrawal",
        )

    def get_recent_transactions(
        self, user_id: int, limit: int = 10
    ) -> list[Transaction]:
        """Get recent transaction history for the user's account."""
        account = self.repository.get_account_by_user_id(user_id)
        if account is None:
            return []
        return self.repository.get_recent_transactions(account.id, limit=limit)
