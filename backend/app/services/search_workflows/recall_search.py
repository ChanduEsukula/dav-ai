from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring import RECALL_REVIEW_SCORE_VERSION
from app.scoring.recall_score import calculate_recall_risk_score
from app.services.openfda_client import OpenFDAClient
from app.services.query_normalization import normalize_safety_query
from app.services.recall_semantic_candidates import build_recall_semantic_candidates
from app.services.semantic_similarity_service import run_semantic_similarity_preview
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
            limit=25,
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
    raw_query: str,
    limit: int,
    error_message: str,
    request_id: str | None,
):
    query_params = {"q": query, "limit": limit}
    if raw_query.strip().lower() != query.lower():
        query_params.update(
            {
                "raw_query": raw_query,
                "normalized_query": query,
                "correction_applied": True,
            }
        )

    audit_event = build_audit_event(
        module="RecallRadar",
        source_id=OPENFDA_DRUG_ENFORCEMENT["source_id"],
        source_name=OPENFDA_DRUG_ENFORCEMENT["source_name"],
        endpoint=OPENFDA_DRUG_ENFORCEMENT["endpoint"],
        query=query,
        query_params=query_params,
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="recall-transform-v0.1",
        score_version=RECALL_REVIEW_SCORE_VERSION,
        error_message=error_message,
    )

    try:
        _save_audit_event_with_request_id(audit_event, request_id=request_id)
    except Exception:
        return None

    return audit_event


def _recall_date_value(record: dict[str, Any]) -> int:
    value = record.get("recall_initiation_date") or ""
    try:
        return int(str(value))
    except ValueError:
        return 0


def _sort_recall_results(
    *,
    records: list[dict[str, Any]],
    sort: str,
    limit: int,
) -> list[dict[str, Any]]:
    if sort == "latest":
        return sorted(records, key=_recall_date_value, reverse=True)[:limit]

    return sorted(
        records,
        key=lambda record: record.get("risk_score", {}).get("score", 0),
        reverse=True,
    )[:limit]


async def execute_recall_search(
    *,
    query: str,
    limit: int,
    request_id: str | None,
    sort: str = "score",
) -> dict[str, Any]:
    """Run RecallRadar search workflow.

    This shared workflow is used by both the RecallRadar API route and
    Saved Monitors manual runs. It fetches openFDA recall data, normalizes
    results, calculates review-priority scores, persists audit metadata, and
    attempts to store a reproducible public-source pull snapshot.
    """

    query_normalization = normalize_safety_query(query, "pharmacy")
    search_query = query_normalization.normalized_query

    try:
        payload = await _search_drug_recalls_with_request_id(
            query=search_query,
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

        normalized_results = _sort_recall_results(
            records=normalized_results,
            sort=sort,
            limit=limit,
        )
        upstream_status = "empty" if not normalized_results else "success"

        audit_event = build_audit_event(
            module="RecallRadar",
            source_id=payload["source_id"],
            source_name=payload["source_name"],
            endpoint=payload["endpoint"],
            query=search_query,
            query_params={
                "q": search_query,
                "raw_query": query_normalization.raw_query,
                "normalized_query": query_normalization.normalized_query,
                "correction_applied": query_normalization.correction_applied,
                "limit": limit,
                "sort": sort,
                "source_limit": 25,
            },
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(normalized_results),
            transform_version="recall-transform-v0.1",
            score_version=RECALL_REVIEW_SCORE_VERSION,
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload=payload["raw"],
            request_id=request_id,
        )

        semantic_result = run_semantic_similarity_preview(
            query_text=search_query,
            records=build_recall_semantic_candidates(normalized_results),
            max_matches=min(limit, 5),
        )

        return {
            "query": search_query,
            "raw_query": query_normalization.raw_query,
            "normalized_query": query_normalization.normalized_query,
            "correction_applied": query_normalization.correction_applied,
            "suggestion_message": query_normalization.suggestion_message,
            "count": len(normalized_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "score_version": RECALL_REVIEW_SCORE_VERSION,
            "sort": sort,
            "medical_disclaimer": "Dav AI provides public-data safety intelligence only. It is not medical advice, diagnostic output, or care guidance.",
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
            "semantic_preview": {
                "query_text": semantic_result.query_text,
                "matches": [
                    {
                        "record_id": match.record_id,
                        "text": match.text,
                        "similarity_score": match.similarity_score,
                        "explanation": match.explanation,
                        "source_name": match.source_name,
                    }
                    for match in semantic_result.matches
                ],
                "limitations": semantic_result.limitations,
                "preview_version": semantic_result.preview_version,
                "is_production_ml": semantic_result.is_production_ml,
            },
            "results": normalized_results,
        }

    except Exception as exc:
        _persist_recall_error_audit(
            query=search_query,
            raw_query=query_normalization.raw_query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
