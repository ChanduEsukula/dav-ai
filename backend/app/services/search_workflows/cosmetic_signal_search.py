from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring import COSMETIC_SIGNAL_SCORE_VERSION
from app.services.official_public_notice_search import search_official_public_notices
from app.services.openfda_cosmetic_event_client import OpenFDACosmeticEventClient
from app.services.query_normalization import normalize_safety_query
from app.sources.registry import OPENFDA_COSMETIC_EVENT

client = OpenFDACosmeticEventClient()


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


def _persist_cosmetic_error_audit(
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
        module="CosmeticSignal",
        source_id=OPENFDA_COSMETIC_EVENT["source_id"],
        source_name=OPENFDA_COSMETIC_EVENT["source_name"],
        endpoint=OPENFDA_COSMETIC_EVENT["endpoint"],
        query=query,
        query_params=query_params,
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="cosmetic-event-transform-v0.1",
        score_version=COSMETIC_SIGNAL_SCORE_VERSION,
        error_message=error_message,
    )

    try:
        _save_audit_event_with_request_id(audit_event, request_id=request_id)
    except Exception:
        return None

    return audit_event


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _extract_reactions(record: dict[str, Any]) -> list[str]:
    return [
        str(reaction)
        for reaction in _as_list(record.get("reactions"))
        if reaction not in (None, "")
    ]


def _extract_outcomes(record: dict[str, Any]) -> list[str]:
    return [
        str(outcome)
        for outcome in _as_list(record.get("outcomes"))
        if outcome not in (None, "")
    ]


def _extract_products(record: dict[str, Any]) -> list[dict[str, Any]]:
    products = record.get("products")
    if not isinstance(products, list):
        return []

    normalized_products = []
    for product in products:
        if not isinstance(product, dict):
            continue

        normalized_products.append(
            {
                "brand_name": product.get("brand_name"),
                "name_brand": product.get("name_brand"),
                "industry_code": product.get("industry_code"),
                "industry_name": product.get("industry_name"),
            }
        )

    return normalized_products


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_number": record.get("report_number"),
        "report_date": record.get("date_started") or record.get("date_created"),
        "serious": record.get("serious"),
        "outcomes": _extract_outcomes(record),
        "reactions": _extract_reactions(record),
        "products": _extract_products(record),
    }


def _calculate_cosmetic_signal_score(
    *,
    record_count: int,
    top_reactions: list[dict[str, Any]],
) -> dict[str, Any]:
    if record_count <= 0:
        concentration = 0.0
    else:
        top_count = top_reactions[0]["count"] if top_reactions else 0
        concentration = round((top_count / record_count) * 100, 2)

    score = 0

    if record_count >= 100:
        score += 35
    elif record_count >= 25:
        score += 25
    elif record_count >= 5:
        score += 15
    elif record_count > 0:
        score += 8

    if concentration >= 75:
        score += 30
    elif concentration >= 50:
        score += 22
    elif concentration >= 25:
        score += 14
    elif concentration > 0:
        score += 8

    if len(top_reactions) >= 5:
        score += 15
    elif len(top_reactions) >= 2:
        score += 8

    score = min(score, 100)

    if score >= 70:
        label = "High"
        priority = "Review closely"
    elif score >= 35:
        label = "Moderate"
        priority = "Watch"
    else:
        label = "Low"
        priority = "Low priority"

    data_confidence = "Limited"
    if record_count >= 100:
        data_confidence = "Moderate"
    if record_count >= 500:
        data_confidence = "Stronger"

    return {
        "score": score,
        "label": label,
        "data_confidence": data_confidence,
        "top_reaction_concentration": concentration,
        "review_priority": priority,
        "score_version": COSMETIC_SIGNAL_SCORE_VERSION,
        "limitations": [
            "Cosmetic adverse-event reports do not prove that a product caused a reaction.",
            "Reports may be incomplete, duplicated, delayed, or influenced by reporting behavior.",
            "Use this as a public-data review signal, not medical advice or an official safety determination.",
        ],
    }


def _normalize_recall_notice(record: Any) -> dict[str, Any]:
    return {
        "title": getattr(record, "title", None),
        "product_name": getattr(record, "product_name", None),
        "brand_name": getattr(record, "brand_name", None),
        "company_name": getattr(record, "company_name", None),
        "category": getattr(record, "category", None),
        "reason": getattr(record, "reason", None) or getattr(record, "hazard_type", None),
        "remedy": getattr(record, "remedy", None),
        "published_date": getattr(record, "published_date", None),
        "record_url": getattr(record, "record_url", None),
        "source_name": getattr(record, "source_name", "FDA Recalls, Market Withdrawals & Safety Alerts"),
        "source_kind": getattr(record, "source_kind", "public_notice"),
        "source_type": getattr(record, "source_type", "public notice page"),
        "extraction_confidence": getattr(record, "extraction_confidence", None),
    }


async def execute_cosmetic_signal_search(
    *,
    query: str,
    limit: int,
    request_id: str | None,
) -> dict[str, Any]:
    query_normalization = normalize_safety_query(query, "cosmetic")
    search_query = query_normalization.normalized_query

    try:
        payload = await client.search_cosmetic_events(
            query=search_query,
            limit=25,
            request_id=request_id,
        )

        recall_notices: list[dict[str, Any]] = []
        recall_source_name: str | None = None
        recall_source_status: str | None = None
        recall_source_error: str | None = None

        try:
            recall_result = await search_official_public_notices(
                query=search_query,
                limit=limit,
                request_id=request_id,
                domain="cosmetic",
            )
            recall_source_name = recall_result.source_name
            recall_source_status = recall_result.upstream_status
            recall_notices = [
                _normalize_recall_notice(record)
                for record in recall_result.records
            ]
        except Exception as exc:
            recall_source_status = "error"
            recall_source_error = str(exc)

        raw_results = payload["raw"].get("results", [])
        upstream_status = "empty" if not raw_results else "success"

        reaction_counter: Counter[str] = Counter()
        normalized_records = []

        for record in raw_results:
            normalized = _normalize_record(record)
            normalized_records.append(normalized)

            for reaction in normalized["reactions"]:
                reaction_counter[reaction] += 1

        top_reactions = [
            {"reaction": reaction, "count": count}
            for reaction, count in sorted(
                reaction_counter.items(),
                key=lambda item: (-item[1], item[0].lower()),
            )[:10]
        ]

        signal_score = _calculate_cosmetic_signal_score(
            record_count=len(raw_results),
            top_reactions=top_reactions,
        )

        audit_event = build_audit_event(
            module="CosmeticSignal",
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
            },
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(raw_results),
            transform_version="cosmetic-event-transform-v0.1",
            score_version=COSMETIC_SIGNAL_SCORE_VERSION,
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload=payload["raw"],
            request_id=request_id,
        )

        return {
            "query": search_query,
            "raw_query": query_normalization.raw_query,
            "normalized_query": query_normalization.normalized_query,
            "correction_applied": query_normalization.correction_applied,
            "suggestion_message": query_normalization.suggestion_message,
            "count": len(raw_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "medical_disclaimer": "Dav AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "cosmetic_disclaimer": "Cosmetic adverse-event reports do not prove that a cosmetic product caused a reaction. Reports may be incomplete, duplicated, delayed, or influenced by reporting patterns.",
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
            "signal_score": signal_score,
            "top_reactions": top_reactions,
            "records": normalized_records[:limit],
            "recall_count": len(recall_notices),
            "recall_source_name": recall_source_name,
            "recall_source_status": recall_source_status,
            "recall_source_error": recall_source_error,
            "recall_notices": recall_notices,
        }

    except Exception as exc:
        _persist_cosmetic_error_audit(
            query=search_query,
            raw_query=query_normalization.raw_query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
