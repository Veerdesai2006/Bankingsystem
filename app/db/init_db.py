from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """
    Create all database tables from the SQLAlchemy model definitions.

    NOTE: In development, we use Alembic for migrations instead.
    This function exists as a fallback/utility for quick setup.
    Alembic is more powerful because it tracks schema changes over time.
    """
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> None:
    """
    Verify that the application can communicate with PostgreSQL.

    HOW IT WORKS:
    ─────────────
    We open a connection and run `SELECT 1` — the simplest possible query.
    If PostgreSQL is running and reachable, it returns [1].
    If not, it raises an exception.

    WHY THIS MATTERS:
    ──────────────────
    The /health/database endpoint uses this to let deployment tools
    (like Docker, Kubernetes, load balancers) verify the app is healthy.
    If this fails, the load balancer stops sending traffic to this instance.

    SECURITY NOTE:
    ───────────────
    This never exposes the DATABASE_URL or any connection details in the
    HTTP response. It only returns {"database": "connected"} or raises
    an internal server error.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))