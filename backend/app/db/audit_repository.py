import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.database import get_database_url

logger = logging.getLogger(__name__)


def save_audit_event(audit_event: dict[str, Any]) -> dict[str, str]:
    database_url = get_database_url()

    if not database_url:
        return {
            "status": "skipped",
            "reason": "database_not_configured",
        }

    audit_event_for_insert = {
        **audit_event,
        "query_params": Jsonb(audit_event.get("query_params", {})),
    }

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into audit_events (
                        audit_id,
                        module,
                        source_id,
                        source_name,
                        endpoint,
                        query,
                        query_params,
                        retrieval_timestamp,
                        upstream_status,
                        record_count,
                        transform_version,
                        score_version,
                        disclaimer_version,
                        error_message,
                        created_at
                    )
                    values (
                        %(audit_id)s,
                        %(module)s,
                        %(source_id)s,
                        %(source_name)s,
                        %(endpoint)s,
                        %(query)s,
                        %(query_params)s,
                        %(retrieval_timestamp)s,
                        %(upstream_status)s,
                        %(record_count)s,
                        %(transform_version)s,
                        %(score_version)s,
                        %(disclaimer_version)s,
                        %(error_message)s,
                        %(created_at)s
                    )
                    """,
                    audit_event_for_insert,
                )

        return {
            "status": "saved",
            "reason": "audit_event_persisted",
        }

    except Exception as exc:
        logger.warning("Audit event persistence failed: %s", exc)

        return {
            "status": "error",
            "reason": "audit_event_persistence_failed",
        }


def list_audit_events(limit: int = 50) -> tuple[str, list[dict[str, Any]]]:
    """
    Return recent audit events.

    Status values:
    - saved: database returned rows
    - skipped: DATABASE_URL is not configured
    - error: database read failed
    """
    database_url = get_database_url()

    if not database_url:
        return "skipped", []

    safe_limit = max(1, min(limit, 100))

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        audit_id,
                        module,
                        source_id,
                        source_name,
                        endpoint,
                        query,
                        query_params,
                        retrieval_timestamp,
                        upstream_status,
                        record_count,
                        transform_version,
                        score_version,
                        disclaimer_version,
                        error_message,
                        created_at
                    from audit_events
                    order by created_at desc
                    limit %s
                    """,
                    (safe_limit,),
                )

                rows = cursor.fetchall()

        return "saved", list(rows)

    except Exception as exc:
        logger.warning("Audit event history read failed: %s", exc)

        return "error", []


def get_audit_event_by_id(audit_id: str) -> tuple[str, dict[str, Any] | None]:
    """
    Return one audit event by audit_id.

    Status values:
    - saved: database lookup completed
    - skipped: DATABASE_URL is not configured
    - error: database read failed
    """
    database_url = get_database_url()

    if not database_url:
        return "skipped", None

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        audit_id,
                        module,
                        source_id,
                        source_name,
                        endpoint,
                        query,
                        query_params,
                        retrieval_timestamp,
                        upstream_status,
                        record_count,
                        transform_version,
                        score_version,
                        disclaimer_version,
                        error_message,
                        created_at
                    from audit_events
                    where audit_id = %s
                    limit 1
                    """,
                    (audit_id,),
                )

                row = cursor.fetchone()

        return "saved", row

    except Exception as exc:
        logger.warning("Audit event detail read failed: %s", exc)

        return "error", None