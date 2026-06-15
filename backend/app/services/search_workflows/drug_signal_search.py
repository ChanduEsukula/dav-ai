from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import get_latest_audit_event_for_query, save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring import DRUG_SIGNAL_SCORE_VERSION
from app.scoring.drug_signal_score import calculate_drug_signal_intelligence_score
from app.scoring.reaction_classifier import (
    REACTION_CLASSIFIER_VERSION,
    classify_reactions,
)
from app.services.drug_signal_semantic_candidates import build_drug_signal_semantic_candidates
from app.services.openfda_drug_event_client import OpenFDADrugEventClient
from app.services.semantic_similarity_service import run_semantic_similarity_preview
from app.sources.registry import OPENFDA_DRUG_EVENT
from app.trends.drug_signal_trend import build_drug_signal_trend_snapshot

client = OpenFDADrugEventClient()


async def _search_drug_events_with_request_id(
    query: str,
    limit: int,
    request_id: str | None,
):
    try:
        return await client.search_drug_events(
            query=query,
            limit=limit,
            request_id=request_id,
        )
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return await client.search_drug_events(query=query, limit=limit)


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


def _get_latest_audit_event_for_query_with_request_id(
    module: str,
    query: str,
    exclude_audit_id: str | None,
    request_id: str | None,
):
    try:
        return get_latest_audit_event_for_query(
            module=module,
            query=query,
            exclude_audit_id=exclude_audit_id,
            request_id=request_id,
        )
    except TypeError as exc:
        if "request_id" not in str(exc) and "exclude_audit_id" not in str(exc):
            raise
        return get_latest_audit_event_for_query(module=module, query=query)


def _persist_drug_event_error_audit(
    *,
    query: str,
    limit: int,
    error_message: str,
    request_id: str | None,
):
    audit_event = build_audit_event(
        module="DrugSignal",
        source_id=OPENFDA_DRUG_EVENT["source_id"],
        source_name=OPENFDA_DRUG_EVENT["source_name"],
        endpoint=OPENFDA_DRUG_EVENT["endpoint"],
        query=query,
        query_params={"q": query, "limit": limit},
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="drug-event-transform-v0.1",
        score_version=DRUG_SIGNAL_SCORE_VERSION,
        error_message=error_message,
    )

    try:
        _save_audit_event_with_request_id(audit_event, request_id=request_id)
    except Exception:
        return None

    return audit_event


async def execute_drug_signal_search(
    *,
    query: str,
    limit: int,
    request_id: str | None,
    sort: str = "reports",
) -> dict[str, Any]:
    """Run DrugSignal search workflow.

    This shared workflow is used by both the DrugSignal API route and
    Saved Monitors manual runs. It fetches openFDA Drug Event data, aggregates
    reported reactions, calculates an explainable signal score, classifies
    reactions, builds a trend snapshot, persists audit metadata, and attempts
    to store a reproducible public-source pull snapshot.
    """

    try:
        payload = await _search_drug_events_with_request_id(
            query=query,
            limit=limit,
            request_id=request_id,
        )
        raw_results = payload["raw"].get("results", [])
        upstream_status = "empty" if not raw_results else "success"

        reaction_counter: Counter[str] = Counter()

        for record in raw_results:
            reactions = record.get("patient", {}).get("reaction", [])

            for reaction in reactions:
                reaction_name = reaction.get("reactionmeddrapt")
                if reaction_name:
                    reaction_counter[reaction_name] += 1

        top_reactions = [
            {"reaction": reaction, "count": count}
            for reaction, count in reaction_counter.most_common(10)
        ]

        if sort == "alpha":
            top_reactions = sorted(
                top_reactions,
                key=lambda item: item["reaction"].lower(),
            )
        else:
            sort = "reports"
            top_reactions = sorted(
                top_reactions,
                key=lambda item: (-item["count"], item["reaction"].lower()),
            )

        intelligence_score = calculate_drug_signal_intelligence_score(
            record_count=len(raw_results),
            top_reactions=top_reactions,
        )
        reaction_categories = classify_reactions(top_reactions)

        audit_event = build_audit_event(
            module="DrugSignal",
            source_id=payload["source_id"],
            source_name=payload["source_name"],
            endpoint=payload["endpoint"],
            query=query,
            query_params={"q": query, "limit": limit, "sort": sort},
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(raw_results),
            transform_version="drug-event-transform-v0.1",
            score_version=DRUG_SIGNAL_SCORE_VERSION,
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload=payload["raw"],
            request_id=request_id,
        )

        _, previous_audit_event = _get_latest_audit_event_for_query_with_request_id(
            module="DrugSignal",
            query=query,
            exclude_audit_id=audit_event["audit_id"],
            request_id=request_id,
        )
        trend_snapshot = build_drug_signal_trend_snapshot(
            current_record_count=len(raw_results),
            previous_event=previous_audit_event,
        )

        semantic_candidates = build_drug_signal_semantic_candidates(
            query=query,
            top_reactions=top_reactions,
            reaction_categories=reaction_categories,
            source_name=payload["source_name"],
        )
        semantic_result = run_semantic_similarity_preview(
            query_text=query,
            records=semantic_candidates,
            max_matches=5,
        )

        return {
            "query": query,
            "count": len(raw_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "medical_disclaimer": "Dav AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "faers_disclaimer": "FAERS adverse-event reports do not prove that a drug caused a reaction. Reports may be incomplete, duplicated, or influenced by reporting patterns.",
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
            "intelligence_score": intelligence_score,
            "reaction_categories": reaction_categories,
            "reaction_classifier_version": REACTION_CLASSIFIER_VERSION,
            "trend_snapshot": trend_snapshot,
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
            "top_reactions": top_reactions,
        }

    except Exception as exc:
        _persist_drug_event_error_audit(
            query=query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
