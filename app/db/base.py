from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    The single root class for all SQLAlchemy models in this project.

    WHY DeclarativeBase (SQLAlchemy 2.0 style)?
    ─────────────────────────────────────────────
    In SQLAlchemy 2.0, we use `DeclarativeBase` instead of the older
    `declarative_base()` function call. It provides better type checking
    and works natively with Python type hints.

    This class intentionally has NO columns.
    Shared columns (id, created_at, updated_at) are defined in:
      - app/models/base.py    → id
      - app/models/mixins.py  → created_at, updated_at

    Keeping this class clean makes it easy to swap databases later.
    """

    pass