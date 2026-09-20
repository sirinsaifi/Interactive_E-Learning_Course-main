"""Alembic environment.

Reads the SQLAlchemy URL from `app.core.config.settings` so migrations
share the same configuration as the application.
"""
from logging.config import fileConfig

from alembic import context

# Make `app` importable when alembic runs from the `backend/` directory.
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import engine as app_engine  # noqa: E402
import app.models  # noqa: F401, E402  -- ensures models are registered on Base.metadata

config = context.config
# Expose the URL for offline mode; online mode reuses the app engine so it
# inherits TLS / connect_args (important for PlanetScale, Aiven, RDS, ...).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with app_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
