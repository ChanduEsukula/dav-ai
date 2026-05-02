import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"

load_dotenv(ENV_PATH)


def get_database_url() -> str | None:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return None

    return database_url.strip() or None


def is_database_configured() -> bool:
    return get_database_url() is not None