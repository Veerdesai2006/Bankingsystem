from datetime import datetime , UTC
from psycopg import Time
from sqlalchemy import DateTime 
from sqlalchemy.orm import mapped_column,Mapped
class TimestampMixin:
    # Automatically adds created_at and updated_at columns
    # to every model that inherits this mixin.
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                    default=datetime.now(UTC))
    updated_at : Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.now(UTC),
                                                onupdate=datetime.now(UTC) , nullable=False
                                                )
    