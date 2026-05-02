import os


def get_database_url() -> str | None:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return None

    return database_url.strip() or None


def is_database_configured() -> bool:
    return get_database_url() is not None