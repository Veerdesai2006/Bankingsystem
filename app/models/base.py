from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class BaseModel(Base, TimestampMixin):
    """
    The base class for EVERY database model in this project.

    Every model that inherits from BaseModel automatically gets:
    ┌─────────────────┬────────────────────────────────────────────────┐
    │ Column          │ Description                                    │
    ├─────────────────┼────────────────────────────────────────────────┤
    │ id              │ Unique integer, auto-incremented by PostgreSQL │
    │ created_at      │ Timestamp when the row was inserted (UTC)      │
    │ updated_at      │ Timestamp when the row was last changed (UTC)  │
    └─────────────────┴────────────────────────────────────────────────┘

    WHY __abstract__ = True?
    ─────────────────────────
    This tells SQLAlchemy: "Do NOT create a table for BaseModel itself."
    BaseModel is a blueprint. Only its subclasses (like AuthUser) get tables.

    INHERITANCE ORDER (Base, TimestampMixin):
    ──────────────────────────────────────────
    Python reads class definitions left to right. Base must come first
    because it is the SQLAlchemy ORM foundation. TimestampMixin adds
    the timestamp columns on top.
    """

    __abstract__ = True

    # Every table in this system gets an auto-incrementing integer primary key.
    # index=True creates a B-tree index for fast lookups by id.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)