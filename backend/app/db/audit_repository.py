import logging
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.database import get_database_url

logger = logging.getLogger("medtrek.audit")


def save_audit_event(
    audit_event: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, str]:
    database_url = get_database_url()
    audit_id = audit_event.get("audit_id")

    logger.info(
        "audit_insert_started",
        extra={
            "event": "audit_insert_started",
            "request_id": request_id,
            "audit_id": audit_id,
            "product_module": audit_event.get("module"),
            "source_id": audit_event.get("source_id"),
            "query": audit_event.get("query"),
        },
    )

    if not database_url:
        logger.info(
            "audit_insert_skipped",
            extra={
                "event": "audit_insert_skipped",
                "request_id": request_id,
                "audit_id": audit_id,
                "product_module": audit_event.get("module"),
                "source_id": audit_event.get("source_id"),
                "reason": "database_not_configured",
            },
        )

        return {
            "status": "skipped",
            "reason": "database_not_configured",
        }

    audit_event_for_insert = {
        **audit_event,
        "query_params": Jsonb(audit_event.get("query_params", {})),
    }

    start_time = time.perf_counter()

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

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "audit_insert_completed",
            extra={
                "event": "audit_insert_completed",
                "request_id": request_id,
                "audit_id": audit_id,
                "product_module": audit_event.get("module"),
                "source_id": audit_event.get("source_id"),
                "status": "saved",
                "duration_ms": duration_ms,
            },
        )

        return {
            "status": "saved",
            "reason": "audit_event_persisted",
        }

    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "audit_insert_failed",
            extra={
                "event": "audit_insert_failed",
                "request_id": request_id,
                "audit_id": audit_id,
                "product_module": audit_event.get("module"),
                "source_id": audit_event.get("source_id"),
                "status": "error",
                "duration_ms": duration_ms,
                "error_category": "audit_event_persistence_failed",
            },
        )

        return {
            "status": "error",
            "reason": "audit_event_persistence_failed",
        }


def list_audit_events(
    limit: int = 50,
    request_id: str | None = None,
    module: str | None = None,
    upstream_status: str | None = None,
    search_text: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Return recent audit events.

    Status values:
    - saved: database returned rows
    - skipped: DATABASE_URL is not configured
    - error: database read failed
    """
    database_url = get_database_url()
    safe_limit = max(1, min(limit, 100))

    logger.info(
        "audit_list_started",
        extra={
            "event": "audit_list_started",
            "request_id": request_id,
            "limit": safe_limit,
            "product_module": module,
            "upstream_status": upstream_status,
            "search_text": search_text,
        },
    )

    if not database_url:
        logger.info(
            "audit_list_skipped",
            extra={
                "event": "audit_list_skipped",
                "request_id": request_id,
                "limit": safe_limit,
                "reason": "database_not_configured",
            },
        )

        return "skipped", []

    start_time = time.perf_counter()

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                filters = []
                params: dict[str, Any] = {"limit": safe_limit}

                if module:
                    filters.append("module = %(module)s")
                    params["module"] = module

                if upstream_status:
                    filters.append("upstream_status = %(upstream_status)s")
                    params["upstream_status"] = upstream_status

                if search_text:
                    filters.append(
                        """
                        (
                            query ilike %(search_pattern)s
                            or audit_id::text ilike %(search_pattern)s
                            or source_name ilike %(search_pattern)s
                            or source_id ilike %(search_pattern)s
                            or transform_version ilike %(search_pattern)s
                            or coalesce(score_version, '') ilike %(search_pattern)s
                        )
                        """
                    )
                    params["search_pattern"] = f"%{search_text}%"

                where_clause = f"where {' and '.join(filters)}" if filters else ""

                cursor.execute(
                    f"""
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
                    {where_clause}
                    order by created_at desc
                    limit %(limit)s
                    """,
                    params,
                )

                rows = cursor.fetchall()

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "audit_list_completed",
            extra={
                "event": "audit_list_completed",
                "request_id": request_id,
                "limit": safe_limit,
                "status": "saved",
                "record_count": len(rows),
                "duration_ms": duration_ms,
            },
        )

        return "saved", list(rows)

    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "audit_list_failed",
            extra={
                "event": "audit_list_failed",
                "request_id": request_id,
                "limit": safe_limit,
                "status": "error",
                "duration_ms": duration_ms,
                "error_category": "audit_event_history_read_failed",
            },
        )

        return "error", []


def get_audit_event_by_id(
    audit_id: str,
    request_id: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """
    Return one audit event by audit_id.

    Status values:
    - saved: database lookup completed
    - skipped: DATABASE_URL is not configured
    - error: database read failed
    """
    database_url = get_database_url()

    logger.info(
        "audit_detail_started",
        extra={
            "event": "audit_detail_started",
            "request_id": request_id,
            "audit_id": audit_id,
        },
    )

    if not database_url:
        logger.info(
            "audit_detail_skipped",
            extra={
                "event": "audit_detail_skipped",
                "request_id": request_id,
                "audit_id": audit_id,
                "reason": "database_not_configured",
            },
        )

        return "skipped", None

    start_time = time.perf_counter()

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

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "audit_detail_completed",
            extra={
                "event": "audit_detail_completed",
                "request_id": request_id,
                "audit_id": audit_id,
                "status": "saved",
                "found": row is not None,
                "duration_ms": duration_ms,
            },
        )

        return "saved", row

    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "audit_detail_failed",
            extra={
                "event": "audit_detail_failed",
                "request_id": request_id,
                "audit_id": audit_id,
                "status": "error",
                "duration_ms": duration_ms,
                "error_category": "audit_event_detail_read_failed",
            },
        )

        return "error", None


def get_latest_audit_event_for_query(
    module: str,
    query: str,
    exclude_audit_id: str | None = None,
    request_id: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """
    Return the latest stored audit event for a module/query pair.

    Status values:
    - saved: database lookup completed
    - skipped: DATABASE_URL is not configured
    - error: database read failed
    """
    database_url = get_database_url()

    logger.info(
        "audit_query_latest_started",
        extra={
            "event": "audit_query_latest_started",
            "request_id": request_id,
            "product_module": module,
            "query": query,
            "exclude_audit_id": exclude_audit_id,
        },
    )

    if not database_url:
        logger.info(
            "audit_query_latest_skipped",
            extra={
                "event": "audit_query_latest_skipped",
                "request_id": request_id,
                "product_module": module,
                "query": query,
                "reason": "database_not_configured",
            },
        )

        return "skipped", None

    start_time = time.perf_counter()

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                params: dict[str, Any] = {
                    "module": module,
                    "query": query,
                }

                exclude_clause = ""

                if exclude_audit_id:
                    exclude_clause = """
                      and audit_id::text != %(exclude_audit_id)s
                    """
                    params["exclude_audit_id"] = exclude_audit_id

                cursor.execute(
                    f"""
                    select
                        audit_id,
                        module,
                        query,
                        record_count,
                        upstream_status,
                        created_at::text as created_at
                    from audit_events
                    where module = %(module)s
                      and lower(query) = lower(%(query)s)
                    {exclude_clause}
                    order by created_at desc
                    limit 1
                    """,
                    params,
                )

                row = cursor.fetchone()

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "audit_query_latest_completed",
            extra={
                "event": "audit_query_latest_completed",
                "request_id": request_id,
                "product_module": module,
                "query": query,
                "status": "saved",
                "found": row is not None,
                "duration_ms": duration_ms,
            },
        )

        return "saved", row

    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "audit_query_latest_failed",
            extra={
                "event": "audit_query_latest_failed",
                "request_id": request_id,
                "product_module": module,
                "query": query,
                "status": "error",
                "duration_ms": duration_ms,
                "error_category": "audit_query_latest_read_failed",
            },
        )

        return "error", None