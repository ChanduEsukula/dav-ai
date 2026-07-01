import hashlib
import json
import logging
import time
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.database import get_database_url, is_deployed_environment

logger = logging.getLogger("dav_ai.source_pulls")


class SourcePullPersistenceError(RuntimeError):
    """Raised when source-pull persistence fails in deployed mode."""


def build_payload_hash(raw_payload: dict[str, Any]) -> str:
    """Build a stable SHA-256 hash for a public-source payload."""

    serialized_payload = json.dumps(
        raw_payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def save_source_pull_with_snapshot(
    *,
    audit_event: dict[str, Any],
    raw_payload: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Persist a reproducible source pull and raw public-source snapshot.

    Status values:
    - saved: source pull and raw snapshot were persisted
    - skipped: DATABASE_URL is not configured
    - error: persistence failed

    This stores public upstream API payloads only. Do not pass PHI, user medical
    history, diagnoses, prescription history, insurance details, or private user data.
    """

    database_url = get_database_url()
    audit_id = audit_event.get("audit_id")
    source_id = audit_event.get("source_id")
    pull_id = str(uuid4())
    snapshot_id = str(uuid4())
    payload_hash = build_payload_hash(raw_payload)

    logger.info(
        "source_pull_insert_started",
        extra={
            "event": "source_pull_insert_started",
            "request_id": request_id,
            "audit_id": audit_id,
            "pull_id": pull_id,
            "source_id": source_id,
            "query": audit_event.get("query"),
        },
    )

    if not database_url:
        logger.info(
            "source_pull_insert_skipped",
            extra={
                "event": "source_pull_insert_skipped",
                "request_id": request_id,
                "audit_id": audit_id,
                "pull_id": pull_id,
                "source_id": source_id,
                "reason": "database_not_configured",
            },
        )
        if is_deployed_environment():
            raise SourcePullPersistenceError(
                "DATABASE_URL must be configured for source-pull persistence in deployed mode."
            )

        return {
            "status": "skipped",
            "reason": "database_not_configured",
            "pull_id": None,
            "snapshot_id": None,
            "payload_hash": payload_hash,
        }

    start_time = time.perf_counter()

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into source_pulls (
                        pull_id,
                        audit_id,
                        source_id,
                        source_name,
                        endpoint,
                        query,
                        query_params,
                        retrieval_timestamp,
                        upstream_status,
                        record_count,
                        payload_hash,
                        transform_version,
                        created_at
                    )
                    values (
                        %(pull_id)s,
                        %(audit_id)s,
                        %(source_id)s,
                        %(source_name)s,
                        %(endpoint)s,
                        %(query)s,
                        %(query_params)s,
                        %(retrieval_timestamp)s,
                        %(upstream_status)s,
                        %(record_count)s,
                        %(payload_hash)s,
                        %(transform_version)s,
                        %(created_at)s
                    )
                    """,
                    {
                        "pull_id": pull_id,
                        "audit_id": audit_id,
                        "source_id": source_id,
                        "source_name": audit_event.get("source_name"),
                        "endpoint": audit_event.get("endpoint"),
                        "query": audit_event.get("query"),
                        "query_params": Jsonb(audit_event.get("query_params", {})),
                        "retrieval_timestamp": audit_event.get("retrieval_timestamp"),
                        "upstream_status": audit_event.get("upstream_status"),
                        "record_count": audit_event.get("record_count", 0),
                        "payload_hash": payload_hash,
                        "transform_version": audit_event.get("transform_version"),
                        "created_at": audit_event.get("created_at"),
                    },
                )

                cursor.execute(
                    """
                    insert into raw_source_snapshots (
                        snapshot_id,
                        pull_id,
                        raw_payload
                    )
                    values (
                        %(snapshot_id)s,
                        %(pull_id)s,
                        %(raw_payload)s
                    )
                    """,
                    {
                        "snapshot_id": snapshot_id,
                        "pull_id": pull_id,
                        "raw_payload": Jsonb(raw_payload),
                    },
                )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "source_pull_insert_completed",
            extra={
                "event": "source_pull_insert_completed",
                "request_id": request_id,
                "audit_id": audit_id,
                "pull_id": pull_id,
                "snapshot_id": snapshot_id,
                "source_id": source_id,
                "status": "saved",
                "duration_ms": duration_ms,
            },
        )

        return {
            "status": "saved",
            "reason": "source_pull_and_snapshot_persisted",
            "pull_id": pull_id,
            "snapshot_id": snapshot_id,
            "payload_hash": payload_hash,
        }

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "source_pull_insert_failed",
            extra={
                "event": "source_pull_insert_failed",
                "request_id": request_id,
                "audit_id": audit_id,
                "pull_id": pull_id,
                "source_id": source_id,
                "status": "error",
                "duration_ms": duration_ms,
                "error_category": "source_pull_persistence_failed",
            },
        )

        if is_deployed_environment():
            raise SourcePullPersistenceError(
                "Source-pull persistence failed in deployed mode."
            ) from exc

        return {
            "status": "error",
            "reason": "source_pull_persistence_failed",
            "pull_id": None,
            "snapshot_id": None,
            "payload_hash": payload_hash,
        }


def get_source_pull_by_audit_id(
    *,
    audit_id: str,
    request_id: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """
    Return metadata-only source pull provenance for one audit event.

    Status values:
    - saved: database read succeeded
    - skipped: DATABASE_URL is not configured
    - error: persistence read failed

    This intentionally does not return raw_source_snapshots.raw_payload.
    """

    database_url = get_database_url()

    if not database_url:
        logger.info(
            "source_pull_read_skipped",
            extra={
                "event": "source_pull_read_skipped",
                "request_id": request_id,
                "audit_id": audit_id,
                "reason": "database_not_configured",
            },
        )
        return "skipped", None

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        sp.pull_id::text as pull_id,
                        sp.audit_id::text as audit_id,
                        sp.source_id,
                        sp.source_name,
                        sp.endpoint,
                        sp.query,
                        sp.query_params,
                        sp.retrieval_timestamp::text as retrieval_timestamp,
                        sp.upstream_status,
                        sp.record_count,
                        sp.payload_hash,
                        sp.transform_version,
                        sp.created_at::text as created_at,
                        rss.snapshot_id::text as snapshot_id
                    from source_pulls sp
                    left join raw_source_snapshots rss
                        on rss.pull_id = sp.pull_id
                    where sp.audit_id = %(audit_id)s
                    order by sp.created_at desc
                    limit 1
                    """,
                    {"audit_id": audit_id},
                )
                row = cursor.fetchone()

        return "saved", row

    except Exception:
        logger.exception(
            "source_pull_read_failed",
            extra={
                "event": "source_pull_read_failed",
                "request_id": request_id,
                "audit_id": audit_id,
                "error_category": "source_pull_read_failed",
            },
        )
        return "error", None
