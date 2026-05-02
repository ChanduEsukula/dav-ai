from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def build_audit_event(
    *,
    module: str,
    source_id: str,
    source_name: str,
    endpoint: str,
    query: str,
    query_params: dict[str, Any],
    retrieval_timestamp: str,
    upstream_status: str,
    record_count: int,
    transform_version: str,
    score_version: str | None = None,
    disclaimer_version: str = "disclaimer-v0.1",
    error_message: str | None = None,
) -> dict[str, Any]:
    return {
        "audit_id": str(uuid4()),
        "module": module,
        "source_id": source_id,
        "source_name": source_name,
        "endpoint": endpoint,
        "query": query,
        "query_params": query_params,
        "retrieval_timestamp": retrieval_timestamp,
        "upstream_status": upstream_status,
        "record_count": record_count,
        "transform_version": transform_version,
        "score_version": score_version,
        "disclaimer_version": disclaimer_version,
        "error_message": error_message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }