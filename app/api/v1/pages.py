from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.dependencies import get_optional_user
from app.db.session import get_db
from app.models.auth_user import AuthUser
from app.repositories.banking_repository import BankingRepository
from app.services.banking_service import BankingService


router = APIRouter(tags=["Pages"])

# Jinja2Templates tells FastAPI where to find our HTML template files.
# Path is relative to where uvicorn is started (the project root).
templates = Jinja2Templates(directory="app/templates")


# ─── Helper ───────────────────────────────────────────────────────────────────


def _get_banking_service(db: Session = Depends(get_db)) -> BankingService:
    return BankingService(BankingRepository(db))


# ─── IMPORTANT: Starlette 1.6+ API Change ────────────────────────────────────
#
# Old API (Starlette < 1.0):
#   templates.TemplateResponse("name.html", {"request": req, "key": val})
#
# New API (Starlette 1.6+):
#   templates.TemplateResponse(request, "name.html", {"key": val})
#
# The request is now the FIRST positional arg, and context does NOT include it.
#


# ─── Public Pages ─────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
):
    """Home page — visible to everyone. Different content for logged-in users."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"current_user": current_user},
    )


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
):
    """Login page. Redirects to dashboard if already authenticated."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"current_user": None},
    )


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
def register_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
):
    """Register page. Redirects to dashboard if already authenticated."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"current_user": None},
    )


# ─── Protected Pages ──────────────────────────────────────────────────────────


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
    service: BankingService = Depends(_get_banking_service),
):
    """Dashboard — requires login. Shows balance and recent transaction history."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    balance = None
    account_number = None
    transactions = []

    try:
        account = service.get_balance(current_user.id)
        balance = account.balance
        account_number = account.account_number
        transactions = service.get_recent_transactions(current_user.id, limit=10)
    except ValueError:
        pass  # No account yet — show empty dashboard with prompt to deposit

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "current_user": current_user,
            "balance": balance,
            "account_number": account_number,
            "transactions": transactions,
        },
    )


@router.get("/balance", response_class=HTMLResponse, include_in_schema=False)
def balance_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
    service: BankingService = Depends(_get_banking_service),
):
    """Balance page — requires login."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    balance = None
    account_number = None
    transactions = []
    error = None

    try:
        account = service.get_balance(current_user.id)
        balance = account.balance
        account_number = account.account_number
        transactions = service.get_recent_transactions(current_user.id, limit=10)
    except ValueError as e:
        error = str(e)

    return templates.TemplateResponse(
        request,
        "balance.html",
        {
            "current_user": current_user,
            "balance": balance,
            "account_number": account_number,
            "transactions": transactions,
            "error": error,
        },
    )


@router.get("/deposit", response_class=HTMLResponse, include_in_schema=False)
def deposit_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
):
    """Deposit page — requires login. Actual deposit is submitted via JS → JSON API."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "deposit.html",
        {"current_user": current_user},
    )


@router.get("/withdraw", response_class=HTMLResponse, include_in_schema=False)
def withdraw_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_optional_user),
    service: BankingService = Depends(_get_banking_service),
):
    """Withdraw page — requires login. Shows current balance for reference."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    balance = None
    try:
        account = service.get_balance(current_user.id)
        balance = account.balance
    except ValueError:
        pass

    return templates.TemplateResponse(
        request,
        "withdraw.html",
        {
            "current_user": current_user,
            "balance": balance,
        },
    )
