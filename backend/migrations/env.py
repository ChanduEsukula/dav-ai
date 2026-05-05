from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Allow Alembic to import backend app modules when run from repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import get_database_url  # noqa: E402


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This project currently manages tables with hand-written migrations,
# not SQLAlchemy ORM models.
target_metadata = None


def get_url() -> str:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in backend/.env before running Alembic."
        )

    # SQLAlchemy needs the psycopg v3 dialect. Hosted Postgres URLs often start
    # with postgresql://, which defaults to psycopg2 unless rewritten.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
