from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# ─── Database Engine ──────────────────────────────────────────────────────────
#
# The engine is the "connection manager" to PostgreSQL.
# Think of it as the pipe between your Python code and the database.
#
# echo=True (development only):
#   Prints every SQL query to the console.
#   Example output: SELECT auth_users.id, auth_users.email FROM auth_users WHERE ...
#   This is invaluable for learning and debugging, but must be OFF in production
#   (it floods your logs).
#
engine = create_engine(
    settings.database_url,
    echo=settings.app_env == "development",
)


# ─── Session Factory ──────────────────────────────────────────────────────────
#
# A "session" is a unit of work with the database.
# Think of it like a shopping cart — you make changes, then either
# commit (save all changes) or rollback (undo all changes).
#
# sessionmaker creates a FACTORY — a callable that produces new sessions.
# We never use SessionLocal directly in routes; we always use get_db() below.
#
# autocommit=False → We control when data is saved (explicit .commit() calls)
# autoflush=False  → We control when pending changes are sent to the DB
#
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ─── Database Dependency ──────────────────────────────────────────────────────
#
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to route handlers.

    HOW IT WORKS (step by step):
    ─────────────────────────────
    1. FastAPI sees `db: Session = Depends(get_db)` in a route function
    2. FastAPI calls get_db() automatically before running the route
    3. A new Session is created from SessionLocal()
    4. The `yield` gives the session to the route handler
    5. The route runs and uses `db` to query/save data
    6. After the route finishes, execution continues after `yield`
    7. The `finally` block closes the session (cleanup)

    WHY try/finally?
    ─────────────────
    The `finally` block runs whether the route succeeded OR raised an error.
    This guarantees we ALWAYS close the session and release the connection
    back to the connection pool. Without this, we'd have "connection leaks."

    USAGE IN ROUTES:
    ─────────────────
        from app.db.session import get_db
        from fastapi import Depends
        from sqlalchemy.orm import Session

        @router.get("/example")
        def my_route(db: Session = Depends(get_db)):
            # db is a live session — use it to query the database
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
