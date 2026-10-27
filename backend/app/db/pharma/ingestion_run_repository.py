from psycopg.types.json import Jsonb
from app.db.pharma.connection import connect


class IngestionRunRepository:
    def start(self, source: str, parameters: dict):
        with connect() as conn:
            return conn.execute(
                "INSERT INTO pharma.ingestion_runs(source, parameters) VALUES (%s, %s) RETURNING id",
                (source, Jsonb(parameters)),
            ).fetchone()['id']

    def finish(self, run_id, *, status: str, counts: dict, coverage: dict, error_summary=None):
        with connect() as conn:
            conn.execute("""
                UPDATE pharma.ingestion_runs SET status=%s, finished_at=now(),
                    records_fetched=%s, records_inserted=%s, records_updated=%s,
                    records_unresolved=%s, records_failed=%s, coverage=%s, error_summary=%s
                WHERE id=%s AND status='running'
            """, (status, counts['fetched'], counts['inserted'], counts['updated'],
                  counts['unresolved'], counts['failed'], Jsonb(coverage), error_summary, run_id))

    def find_by_id(self, run_id):
        with connect() as conn:
            return conn.execute("SELECT * FROM pharma.ingestion_runs WHERE id=%s", (run_id,)).fetchone()
