from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import check_database_connection


app = FastAPI(
    title="SecureBank API",
    description="Backend API for the SecureBank net-banking system.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "SecureBank API is running",
        "environment": settings.app_env,
    }


@app.get("/health/database")
def database_health():
    """Confirm that the API can connect to PostgreSQL without exposing credentials."""
    check_database_connection()
    return {"database": "connected"}
