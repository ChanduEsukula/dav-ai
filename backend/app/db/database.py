import os
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"
MEMORY_FALLBACK_WARNING = "Memory fallback is demo-only and not durable."
DEPLOYED_ENVIRONMENT_VALUES = {"prod", "production", "staging", "preview"}
PersistenceMode = Literal["database", "memory_fallback"]


class PersistenceVisibility(TypedDict):
    persistence_mode: PersistenceMode
    durable_persistence: bool
    warning: str | None


load_dotenv(ENV_PATH)


def get_database_url() -> str | None:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return None

    return database_url.strip() or None


def is_database_configured() -> bool:
    return get_database_url() is not None


def is_deployed_environment() -> bool:
    """Return True when runtime config should fail closed instead of demo-fallback."""

    for name in ("DAVAI_ENV", "APP_ENV", "ENVIRONMENT", "PYTHON_ENV"):
        if os.getenv(name, "").strip().lower() in DEPLOYED_ENVIRONMENT_VALUES:
            return True

    return os.getenv("RENDER", "").strip().lower() == "true"


def get_persistence_visibility(database_configured: bool | None = None) -> PersistenceVisibility:
    configured = is_database_configured() if database_configured is None else database_configured

    if configured:
        return {
            "persistence_mode": "database",
            "durable_persistence": True,
            "warning": None,
        }

    return {
        "persistence_mode": "memory_fallback",
        "durable_persistence": False,
        "warning": MEMORY_FALLBACK_WARNING,
    }
