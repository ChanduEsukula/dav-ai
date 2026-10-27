import psycopg
from psycopg.rows import dict_row
from app.db.database import get_database_url


class PharmaceuticalDatabaseUnavailable(RuntimeError):
    pass


def connect():
    url = get_database_url()
    if not url:
        raise PharmaceuticalDatabaseUnavailable("Pharmaceutical catalog requires PostgreSQL")
    return psycopg.connect(url, row_factory=dict_row)
