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