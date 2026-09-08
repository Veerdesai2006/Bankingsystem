from datetime import datetime, UTC

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    A mixin that adds `created_at` and `updated_at` to any model.

    WHAT IS A MIXIN?
    ─────────────────
    A mixin is a class that you "mix in" to another class using multiple
    inheritance to give it extra capabilities. You never use TimestampMixin
    alone — you always combine it with a real model class.

    THE CRITICAL BUG THIS FIXES:
    ──────────────────────────────
    Original code had:
        default=datetime.now(UTC)

    Python evaluates this ONCE when the file is first imported.
    Every row would get the SAME timestamp — the time the server started!

    The fix:
        default=lambda: datetime.now(UTC)

    A lambda is a tiny function. SQLAlchemy calls it each time it inserts
    a new row. So every row gets its own fresh timestamp. ✓

    WHY timezone=True?
    ───────────────────
    Always store timestamps with timezone info (UTC).
    Without it, you get "naive" datetimes that cause bugs when your
    server is in a different timezone than your database.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )