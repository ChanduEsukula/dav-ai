from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring.recall_score import calculate_recall_risk_score
from app.services.openfda_client import OpenFDAClient
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT

client = OpenFDAClient()


async def _search_drug_recalls_with_request_id(
    query: str,
    limit: int,
    request_id: str | None,
):
    try:
        return await client.search_drug_recalls(
            query=query,
            limit=limit,
            request_id=request_id,
        )
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return await client.search_drug_recalls(query=query, limit=limit)


def _save_audit_event_with_request_id(audit_event, request_id: str | None):
    try:
        return save_audit_event(audit_event, request_id=request_id)
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return save_audit_event(audit_event)


def _save_source_pull_with_request_id(
    *,
    audit_event: dict[str, Any],
    raw_payload: dict[str, Any],
    request_id: str | None,
):
    try:
        return save_source_pull_with_snapshot(
            audit_event=audit_event,
            raw_payload=raw_payload,
            request_id=request_id,
        )
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return save_source_pull_with_snapshot(
            audit_event=audit_event,
            raw_payload=raw_payload,
        )


def _persist_recall_error_audit(
    *,
    query: str,
    limit: int,
    error_message: str,
    request_id: str | None,
):
    audit_event = build_audit_event(
        module="RecallRadar",
        source_id=OPENFDA_DRUG_ENFORCEMENT["source_id"],
        source_name=OPENFDA_DRUG_ENFORCEMENT["source_name"],
        endpoint=OPENFDA_DRUG_ENFORCEMENT["endpoint"],
        query=query,
        query_params={"q": query, "limit": limit},
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="recall-transform-v0.1",
        score_version="recall-risk-v0.1",
        error_message=error_message,
    )

    try:
        _save_audit_event_with_request_id(audit_event, request_id=request_id)
    except Exception:
        return None

    return audit_event


async def execute_recall_search(
    *,
    query: str,
    limit: int,
    request_id: str | None,
) -> dict[str, Any]:
    """Run RecallRadar search workflow.

    This shared workflow is used by both the RecallRadar API route and
    Saved Monitors manual runs. It fetches openFDA recall data, normalizes
    results, calculates review-priority scores, persists audit metadata, and
    attempts to store a reproducible public-source pull snapshot.
    """

    try:
        payload = await _search_drug_recalls_with_request_id(
            query=query,
            limit=limit,
            request_id=request_id,
        )
        raw_results = payload["raw"].get("results", [])
        upstream_status = "empty" if not raw_results else "success"

        normalized_results = []

        for record in raw_results:
            risk = calculate_recall_risk_score(record)

            normalized_results.append(
                {
                    "recall_number": record.get("recall_number"),
                    "product_description": record.get("product_description"),
                    "reason_for_recall": record.get("reason_for_recall"),
                    "classification": record.get("classification"),
                    "status": record.get("status"),
                    "recall_initiation_date": record.get("recall_initiation_date"),
                    "distribution_pattern": record.get("distribution_pattern"),
                    "recalling_firm": record.get("recalling_firm"),
                    "risk_score": risk,
                    "source": {
                        "name": payload["source_name"],
                        "endpoint": payload["endpoint"],
                        "retrieval_timestamp": payload["retrieval_timestamp"],
                    },
                }
            )

        audit_event = build_audit_event(
            module="RecallRadar",
            source_id=payload["source_id"],
            source_name=payload["source_name"],
            endpoint=payload["endpoint"],
            query=query,
            query_params={"q": query, "limit": limit},
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(normalized_results),
            transform_version="recall-transform-v0.1",
            score_version="recall-risk-v0.1",
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload=payload["raw"],
            request_id=request_id,
        )

        return {
            "query": query,
            "count": len(normalized_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "score_version": "recall-risk-v0.1",
            "medical_disclaimer": "Dav AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "audit": {
                "audit_id": audit_event["audit_id"],
                "source_id": audit_event["source_id"],
                "module": audit_event["module"],
                "upstream_status": audit_event["upstream_status"],
                "record_count": audit_event["record_count"],
                "transform_version": audit_event["transform_version"],
                "source_snapshot_status": source_pull_result["status"],
                "source_pull_id": source_pull_result["pull_id"],
                "source_payload_hash": source_pull_result["payload_hash"],
            },
            "results": normalized_results,
        }

    except Exception as exc:
        _persist_recall_error_audit(
            query=query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
