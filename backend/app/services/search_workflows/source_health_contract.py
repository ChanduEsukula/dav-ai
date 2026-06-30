from __future__ import annotations

from typing import Any


SOURCE_KIND_VALUES = {"structured_api", "public_notice", "normalized_public_notice"}


def validate_real_world_source_health_contract(body: dict[str, Any]) -> list[str]:
    """Validate RealWorldSafety source-health metadata.

    Returns a list of readable contract errors. An empty list means the response
    satisfies the source-health contract.
    """

    errors: list[str] = []

    sources_checked = body.get("sources_checked") or []
    sources_failed = body.get("sources_failed") or []
    source_audits = body.get("source_audits") or []
    source_freshness = body.get("source_freshness") or []
    checked_at = body.get("retrieval_timestamp")

    checked_source_ids = {
        source.get("source_id") for source in sources_checked if source.get("source_id")
    }
    failed_source_ids = {
        source.get("source_id") for source in sources_failed if source.get("source_id")
    }
    freshness_source_ids = {
        freshness.get("source_id") for freshness in source_freshness if freshness.get("source_id")
    }

    if not checked_source_ids and not failed_source_ids:
        errors.append("expected at least one checked or failed source")

    expected_freshness_ids = checked_source_ids | failed_source_ids
    if freshness_source_ids != expected_freshness_ids:
        errors.append(
            "source_freshness source_ids must match checked and failed source_ids "
            f"(expected={sorted(expected_freshness_ids)}, actual={sorted(freshness_source_ids)})"
        )

    for index, source in enumerate(sources_checked):
        errors.extend(_validate_checked_source(source, index=index))

    for index, source in enumerate(sources_failed):
        errors.extend(_validate_failed_source(source, index=index))

    for index, audit in enumerate(source_audits):
        errors.extend(_validate_source_audit(audit, index=index))

    for index, freshness in enumerate(source_freshness):
        errors.extend(
            _validate_source_freshness(
                freshness,
                index=index,
                expected_checked_at=checked_at,
            )
        )

    return errors


def _validate_checked_source(source: dict[str, Any], *, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"sources_checked[{index}]"

    _require_text(errors, source, "source_id", prefix)
    _require_text(errors, source, "source_name", prefix)
    _require_text(errors, source, "source_type", prefix)
    _require_text(errors, source, "source_url", prefix)
    _require_source_kind(errors, source, prefix)
    _require_text(errors, source, "upstream_status", prefix)
    _require_non_negative_int(errors, source, "record_count", prefix)

    return errors


def _validate_failed_source(source: dict[str, Any], *, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"sources_failed[{index}]"

    _require_text(errors, source, "source_id", prefix)
    _require_text(errors, source, "source_name", prefix)
    _require_text(errors, source, "source_type", prefix)
    _require_text(errors, source, "source_url", prefix)
    _require_source_kind(errors, source, prefix)
    _require_text(errors, source, "error_type", prefix)
    _require_text(errors, source, "reason", prefix)

    return errors


def _validate_source_audit(audit: dict[str, Any], *, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"source_audits[{index}]"

    _require_text(errors, audit, "audit_id", prefix)
    _require_text(errors, audit, "source_id", prefix)
    _require_text(errors, audit, "source_name", prefix)
    _require_text(errors, audit, "upstream_status", prefix)
    _require_non_negative_int(errors, audit, "record_count", prefix)
    _require_text(errors, audit, "transform_version", prefix)

    if audit.get("module") != "RealWorldSafety":
        errors.append(f"{prefix}.module must be RealWorldSafety")

    return errors


def _validate_source_freshness(
    freshness: dict[str, Any],
    *,
    index: int,
    expected_checked_at: str | None,
) -> list[str]:
    errors: list[str] = []
    prefix = f"source_freshness[{index}]"

    _require_text(errors, freshness, "source_id", prefix)
    _require_text(errors, freshness, "source_name", prefix)
    _require_text(errors, freshness, "source_type", prefix)
    _require_source_kind(errors, freshness, prefix)
    _require_text(errors, freshness, "upstream_status", prefix)
    _require_non_negative_int(errors, freshness, "record_count", prefix)
    _require_text(errors, freshness, "freshness_status", prefix)
    _require_text(errors, freshness, "user_label", prefix)
    _require_text(errors, freshness, "explanation", prefix)

    if freshness.get("checked_at") != expected_checked_at:
        errors.append(f"{prefix}.checked_at must match retrieval_timestamp")

    return errors


def _require_text(
    errors: list[str],
    payload: dict[str, Any],
    field: str,
    prefix: str,
) -> None:
    if not isinstance(payload.get(field), str) or not payload.get(field).strip():
        errors.append(f"{prefix}.{field} is required")


def _require_source_kind(errors: list[str], payload: dict[str, Any], prefix: str) -> None:
    if payload.get("source_kind") not in SOURCE_KIND_VALUES:
        errors.append(f"{prefix}.source_kind must be one of {sorted(SOURCE_KIND_VALUES)}")


def _require_non_negative_int(
    errors: list[str],
    payload: dict[str, Any],
    field: str,
    prefix: str,
) -> None:
    value = payload.get(field)
    if not isinstance(value, int) or value < 0:
        errors.append(f"{prefix}.{field} must be a non-negative integer")
