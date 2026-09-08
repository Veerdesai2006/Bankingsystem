from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth as auth_router
from app.api.v1 import banking as banking_router
from app.api.v1 import pages as pages_router
from app.core.config import settings
from app.db.init_db import check_database_connection


# ─── Application Factory ──────────────────────────────────────────────────────

app = FastAPI(
    title="SecureBank API",
    description="""
    Backend API for the SecureBank net-banking system.

    **Architecture:**
    - Browser → Jinja2 Pages (HTML) → JSON API → Service → Repository → PostgreSQL

    **Authentication:**
    - Register: POST /api/v1/auth/register
    - Login:    POST /api/v1/auth/login  (sets HTTP-only cookie)
    - Logout:   POST /api/v1/auth/logout

    **Banking (requires login):**
    - Balance:      GET  /api/v1/banking/balance
    - Deposit:      POST /api/v1/banking/deposit
    - Withdraw:     POST /api/v1/banking/withdraw
    - Transactions: GET  /api/v1/banking/transactions
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── Static Files ─────────────────────────────────────────────────────────────
#
# This mounts the app/static/ directory so templates can use:
#   {{ url_for('static', path='css/style.css') }}
#   {{ url_for('static', path='js/main.js') }}
#
# Files are served at /static/css/style.css, /static/js/main.js, etc.
#
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ─── API Routers ──────────────────────────────────────────────────────────────
#
# All JSON API routes live under /api/v1/ prefix.
# This lets us version our API in the future (v2, v3...) without breaking v1.
#
app.include_router(auth_router.router,    prefix="/api/v1")
app.include_router(banking_router.router, prefix="/api/v1")


# ─── Page Routers ─────────────────────────────────────────────────────────────
#
# HTML page routes have no prefix — they respond to /, /login, /dashboard, etc.
# They use Jinja2 to render HTML templates.
#
# IMPORTANT: Pages router MUST be registered AFTER the API routers
# to avoid the catch-all "/" route intercepting API requests.
#
app.include_router(pages_router.router)


# ─── Health Check Endpoints ───────────────────────────────────────────────────


@app.get("/api/health", tags=["Health"])
def health_check():
    """Basic health check — confirms the app is running."""
    return {
        "status": "ok",
        "environment": settings.app_env,
        "docs": "/docs",
    }


@app.get("/api/health/database", tags=["Health"])
def database_health():
    """
    Confirms PostgreSQL connectivity.
    Used by deployment tools and monitoring systems.

    SECURITY: Never exposes credentials or internal errors.
    Returns {"database": "connected"} on success.
    Raises 500 on failure (caught by FastAPI's default error handler).
    """
    check_database_connection()
    return {"database": "connected"}
