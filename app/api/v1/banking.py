from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth_user import AuthUser
from app.repositories.banking_repository import BankingRepository
from app.schemas.banking import (
    BalanceResponse,
    DepositRequest,
    TransactionResponse,
    WithdrawRequest,
)
from app.services.banking_service import BankingService


router = APIRouter(
    prefix="/banking",
    tags=["Banking"],
)


def _get_service(db: Session = Depends(get_db)) -> BankingService:
    """
    Dependency factory for BankingService.

    Instead of repeating `BankingRepository(db)` and `BankingService(repo)`
    in every route, we define it once here. FastAPI injects it automatically.

    This is a common FastAPI pattern called a "dependency factory."
    """
    repository = BankingRepository(db)
    return BankingService(repository)


@router.get(
    "/balance",
    response_model=BalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Check your current account balance",
)
def check_balance(
    current_user: AuthUser = Depends(get_current_user),
    service: BankingService = Depends(_get_service),
) -> BalanceResponse:
    """
    Returns the current balance of the authenticated user's bank account.

    HOW AUTHENTICATION WORKS HERE:
    ────────────────────────────────
    `current_user: AuthUser = Depends(get_current_user)` tells FastAPI:
      "Before running this function, call get_current_user().
       If it raises an exception → return 401 immediately.
       If it succeeds → inject the AuthUser object as `current_user`."

    So by the time this function runs, we KNOW the user is logged in
    and active. No manual authentication check needed.
    """
    try:
        account = service.get_balance(current_user.id)
        return BalanceResponse(
            account_number=account.account_number,
            balance=account.balance,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deposit money into your account",
)
def deposit(
    request: DepositRequest,
    current_user: AuthUser = Depends(get_current_user),
    service: BankingService = Depends(_get_service),
) -> TransactionResponse:
    """
    Deposit money into the authenticated user's account.

    VALIDATION LAYERS:
    ───────────────────
    Layer 1 (Pydantic): amount must be a valid Decimal and > 0
    Layer 2 (Service):  account must be active

    If both pass → balance is updated → transaction is recorded → response is returned.
    """
    try:
        transaction = service.deposit(current_user.id, request)
        return TransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            description=transaction.description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/withdraw",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw money from your account",
)
def withdraw(
    request: WithdrawRequest,
    current_user: AuthUser = Depends(get_current_user),
    service: BankingService = Depends(_get_service),
) -> TransactionResponse:
    """
    Withdraw money from the authenticated user's account.

    EXTRA VALIDATION vs DEPOSIT:
    ──────────────────────────────
    Withdrawal checks: amount <= current_balance
    If not enough funds → 400 Bad Request with a helpful message.
    """
    try:
        transaction = service.withdraw(current_user.id, request)
        return TransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            description=transaction.description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "/transactions",
    response_model=list[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent transaction history",
)
def get_transactions(
    limit: int = 10,
    current_user: AuthUser = Depends(get_current_user),
    service: BankingService = Depends(_get_service),
) -> list[TransactionResponse]:
    """
    Return the N most recent transactions for the authenticated user.
    Default: last 10 transactions. Max recommended: 50.
    """
    transactions = service.get_recent_transactions(current_user.id, limit=limit)
    return [
        TransactionResponse(
            id=t.id,
            transaction_type=t.transaction_type,
            amount=t.amount,
            balance_after=t.balance_after,
            description=t.description,
        )
        for t in transactions
    ]
