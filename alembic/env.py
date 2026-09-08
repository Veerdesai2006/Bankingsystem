from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base

# Import ALL models so Alembic can detect them for autogenerate.
# If you add a new model, you MUST import it here (or add to app/models/__init__.py).
import app.models  # noqa: F401  ← This imports AuthUser, BankAccount, Transaction

# ─── Alembic Config ───────────────────────────────────────────────────────────

config = context.config

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our SQLAlchemy metadata (the table definitions)
target_metadata = Base.metadata


# ─── Database URL from .env ───────────────────────────────────────────────────
#
# Instead of reading sqlalchemy.url from alembic.ini (which would be hardcoded),
# we read from our Pydantic settings which reads from the .env file.
# This means you only need to set DATABASE_URL in .env — one single source of truth.
#
def get_url() -> str:
    return settings.database_url


# ─── Offline Mode ─────────────────────────────────────────────────────────────
#
# Offline mode generates a migration SQL script WITHOUT connecting to the database.
# Useful for reviewing what SQL Alembic would run, or running in CI/CD pipelines.
#
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,       # Detect column type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ─── Online Mode ──────────────────────────────────────────────────────────────
#
# Online mode connects to the live database and runs migrations directly.
# This is what you use during development with `alembic upgrade head`.
#
def run_migrations_online() -> None:
    """Run migrations in 'online' mode (live database connection)."""
    # Override the sqlalchemy.url with our value from .env
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ─── Run ──────────────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
