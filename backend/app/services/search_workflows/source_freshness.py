from __future__ import annotations

from typing import Any


def _humanize(value: str | None) -> str:
    if not value:
        return "Not listed"
    return value.replace("_", " ")


def _status_payload(
    *,
    upstream_status: str,
    source_snapshot_status: str | None,
    source_pull_id: str | None,
    source_payload_hash: str | None,
    failed_reason: str | None = None,
) -> tuple[str, str, str]:
    if failed_reason or upstream_status == "error":
        return (
            "source_issue_reported",
            "Source issue reported",
            failed_reason or "DavAI attempted to check this source, but the source reported an issue.",
        )

    if source_snapshot_status == "stored" or source_pull_id or source_payload_hash:
        return (
            "pulled_and_stored",
            "Pulled and stored",
            "DavAI checked this public source and stored audit metadata for the returned payload.",
        )

    if upstream_status == "success":
        return (
            "checked_during_search",
            "Checked during this search",
            "DavAI checked this public source while serving the search response.",
        )

    if upstream_status == "empty":
        return (
            "checked_no_records",
            "Checked; no records returned",
            "DavAI checked this public source, but it returned no matching records for this query.",
        )

    return (
        "checked_status_unknown",
        _humanize(upstream_status),
        "DavAI recorded this source status from the public safety search workflow.",
    )


def build_source_freshness(
    *,
    sources_checked: list[dict[str, Any]],
    sources_failed: list[dict[str, Any]],
    source_audits: list[dict[str, Any]],
    checked_at: str,
) -> list[dict[str, Any]]:
    audits_by_source_id = {audit.get("source_id"): audit for audit in source_audits}
    failed_by_source_id = {source.get("source_id"): source for source in sources_failed}
    freshness: list[dict[str, Any]] = []

    for source in sources_checked:
        source_id = source.get("source_id")
        audit = audits_by_source_id.get(source_id, {})
        failed = failed_by_source_id.get(source_id)

        freshness_status, user_label, explanation = _status_payload(
            upstream_status=source.get("upstream_status", "unknown"),
            source_snapshot_status=audit.get("source_snapshot_status"),
            source_pull_id=audit.get("source_pull_id"),
            source_payload_hash=audit.get("source_payload_hash"),
            failed_reason=failed.get("reason") if failed else None,
        )

        freshness.append(
            {
                "source_id": source_id,
                "source_name": source.get("source_name"),
                "source_type": source.get("source_type"),
                "source_kind": source.get("source_kind"),
                "upstream_status": source.get("upstream_status", "unknown"),
                "record_count": source.get("record_count", 0),
                "freshness_status": freshness_status,
                "user_label": user_label,
                "explanation": explanation,
                "source_snapshot_status": audit.get("source_snapshot_status"),
                "source_pull_id": audit.get("source_pull_id"),
                "source_payload_hash": audit.get("source_payload_hash"),
                "checked_at": checked_at,
            }
        )

    checked_ids = {source.get("source_id") for source in sources_checked}
    for source in sources_failed:
        if source.get("source_id") in checked_ids:
            continue

        freshness_status, user_label, explanation = _status_payload(
            upstream_status="error",
            source_snapshot_status=None,
            source_pull_id=None,
            source_payload_hash=None,
            failed_reason=source.get("reason"),
        )

        freshness.append(
            {
                "source_id": source.get("source_id"),
                "source_name": source.get("source_name"),
                "source_type": source.get("source_type"),
                "source_kind": source.get("source_kind"),
                "upstream_status": "error",
                "record_count": 0,
                "freshness_status": freshness_status,
                "user_label": user_label,
                "explanation": explanation,
                "source_snapshot_status": None,
                "source_pull_id": None,
                "source_payload_hash": None,
                "checked_at": checked_at,
            }
        )

    return freshness
