from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.models.transaction import Transaction, TransactionType


class BankingRepository:
    """
    Handles all database operations for banking (accounts and transactions).

    LAYER RULE: Zero business logic here.
    This class only knows HOW to read/write banking data.
    It does NOT know WHETHER it should.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ─── Account Operations ───────────────────────────────────────────────────

    def get_account_by_user_id(self, user_id: int) -> BankAccount | None:
        """Get the bank account for a given user ID."""
        statement = select(BankAccount).where(BankAccount.user_id == user_id)
        result = self.db.execute(statement)
        return result.scalar_one_or_none()

    def get_account_by_number(self, account_number: str) -> BankAccount | None:
        """Get an account by its account number string (e.g., 'ACC1234567890')."""
        statement = select(BankAccount).where(
            BankAccount.account_number == account_number
        )
        result = self.db.execute(statement)
        return result.scalar_one_or_none()

    def create_account(
        self, *, user_id: int, account_number: str
    ) -> BankAccount:
        """Create a new bank account starting with ₹0.00 balance."""
        account = BankAccount(
            user_id=user_id,
            account_number=account_number,
            balance=Decimal("0.00"),
            is_active=True,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_balance(
        self, account: BankAccount, new_balance: Decimal
    ) -> BankAccount:
        """
        Update the balance of an existing account.

        WHY PASS THE ACCOUNT OBJECT (not just user_id)?
        ──────────────────────────────────────────────────
        The service has already fetched and validated the account.
        Passing it directly avoids a second database query.
        We modify the object in-place → commit → refresh.
        """
        account.balance = new_balance
        self.db.commit()
        self.db.refresh(account)
        return account

    # ─── Transaction Operations ───────────────────────────────────────────────

    def create_transaction(
        self,
        *,
        account_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_after: Decimal,
        description: str | None = None,
    ) -> Transaction:
        """
        Create a permanent transaction record.

        WHEN IS THIS CALLED?
        ─────────────────────
        AFTER the balance has been successfully updated.
        The sequence in BankingService:
            1. Validate the request
            2. Calculate new balance
            3. update_balance()           ← save new balance
            4. create_transaction()       ← record what happened
            5. Return the transaction

        If step 3 fails, we never reach step 4.
        If step 3 succeeds but step 4 fails (very rare), the balance
        was updated but no record exists. This is a known V1 limitation.
        In production banking, steps 3 and 4 would be in a single
        database transaction (using db.begin()) for atomicity.
        """
        transaction = Transaction(
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            description=description,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_recent_transactions(
        self, account_id: int, limit: int = 10
    ) -> list[Transaction]:
        """
        Return the N most recent transactions for an account.
        Ordered newest-first (ORDER BY created_at DESC).
        """
        statement = (
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        result = self.db.execute(statement)
        return list(result.scalars().all())
