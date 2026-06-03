from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring.recall_score import calculate_recall_risk_score
from app.services.foodradar_search_intent import FoodRadarSearchIntent, classify_foodradar_search_intent
from app.services.openfda_food_enforcement_client import OpenFDAFoodEnforcementClient
from app.services.usda_fsis_recall_client import USDAFSISRecallClient
from app.sources.registry import OPENFDA_FOOD_ENFORCEMENT, USDA_FSIS_RECALL

food_client = OpenFDAFoodEnforcementClient()
fsis_client = USDAFSISRecallClient()


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


def _persist_food_error_audit(
    *,
    query: str,
    limit: int,
    error_message: str,
    request_id: str | None,
):
    audit_event = build_audit_event(
        module="FoodRadar",
        source_id="foodradar_multi_source",
        source_name="FoodRadar multi-source search",
        endpoint="openFDA Food Enforcement + USDA FSIS Recall API",
        query=query,
        query_params={"category": "food_supplement", "q": query, "limit": limit},
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="everyday-safety-food-transform-v0.2",
        score_version="recall-risk-v0.1",
        error_message=error_message,
    )

    try:
        _save_audit_event_with_request_id(audit_event, request_id=request_id)
    except Exception:
        return None

    return audit_event


def _get_first_value(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize_fda_record(
    *,
    record: dict[str, Any],
    index: int,
    payload: dict[str, Any],
    search_strategy_used: str,
) -> dict[str, Any]:
    risk = calculate_recall_risk_score(record)

    return {
        "record_id": record.get("event_id") or record.get("recall_number") or f"fda-{index}",
        "recall_number": record.get("recall_number"),
        "product_description": record.get("product_description"),
        "reason_for_recall": record.get("reason_for_recall"),
        "classification": record.get("classification"),
        "status": record.get("status"),
        "recall_initiation_date": record.get("recall_initiation_date"),
        "report_date": record.get("report_date"),
        "distribution_pattern": record.get("distribution_pattern"),
        "recalling_firm": record.get("recalling_firm"),
        "product_quantity": record.get("product_quantity"),
        "code_info": record.get("code_info"),
        "source_type": "FDA_FOOD_ENFORCEMENT",
        "search_strategy_used": search_strategy_used,
        "risk_score": risk,
        "source": {
            "name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
        },
    }


def _normalize_fsis_record(
    *,
    record: dict[str, Any],
    index: int,
    payload: dict[str, Any],
    search_strategy_used: str,
) -> dict[str, Any]:
    normalized_for_score = {
        "classification": _get_first_value(
            record,
            (
                "field_recall_classification",
                "recall_classification",
                "classification",
                "field_recall_type",
            ),
        ),
        "status": _get_first_value(
            record,
            (
                "field_active_notice",
                "active_notice",
                "status",
                "field_status",
            ),
        ),
        "recall_initiation_date": _get_first_value(
            record,
            (
                "field_recall_date",
                "recall_date",
                "field_publication_date",
                "publication_date",
            ),
        ),
        "distribution_pattern": _get_first_value(
            record,
            (
                "field_states",
                "states",
                "field_distribution_list",
                "distribution",
            ),
        ),
    }

    risk = calculate_recall_risk_score(normalized_for_score)

    product_description = _get_first_value(
        record,
        (
            "field_product_items",
            "product_items",
            "field_product",
            "product",
            "title",
            "recall_title",
            "field_title",
        ),
    )

    reason_for_recall = _get_first_value(
        record,
        (
            "field_recall_reason",
            "recall_reason",
            "field_reason",
            "reason",
            "summary",
            "body",
        ),
    )

    return {
        "record_id": str(
            _get_first_value(
                record,
                (
                    "id",
                    "uuid",
                    "field_recall_number",
                    "recall_number",
                    "field_recall_id",
                ),
            )
            or f"fsis-{index}"
        ),
        "recall_number": _get_first_value(
            record,
            ("field_recall_number", "recall_number", "field_recall_id"),
        ),
        "product_description": product_description,
        "reason_for_recall": reason_for_recall,
        "classification": normalized_for_score["classification"],
        "status": normalized_for_score["status"],
        "recall_initiation_date": normalized_for_score["recall_initiation_date"],
        "report_date": _get_first_value(
            record,
            ("field_publication_date", "publication_date", "created", "changed"),
        ),
        "distribution_pattern": normalized_for_score["distribution_pattern"],
        "recalling_firm": _get_first_value(
            record,
            (
                "field_establishment",
                "establishment",
                "field_company",
                "company",
                "recalling_firm",
            ),
        ),
        "product_quantity": _get_first_value(
            record,
            ("field_pounds_recalled", "pounds_recalled", "product_quantity"),
        ),
        "code_info": _get_first_value(
            record,
            ("field_labels", "labels", "field_product_labels", "code_info"),
        ),
        "source_type": "USDA_FSIS_RECALL",
        "search_strategy_used": search_strategy_used,
        "risk_score": risk,
        "source": {
            "name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
        },
    }


def _checked_source(
    *,
    payload: dict[str, Any],
    source_type: str,
    record_count: int,
) -> dict[str, Any]:
    upstream_status = payload.get("upstream_status")
    if upstream_status not in {"success", "empty", "error"}:
        upstream_status = "success" if record_count else "empty"

    return {
        "source_id": payload["source_id"],
        "source_name": payload["source_name"],
        "source_type": source_type,
        "endpoint": payload["endpoint"],
        "upstream_status": upstream_status,
        "record_count": record_count,
    }


def _record_search_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("product_description"),
        record.get("reason_for_recall"),
        record.get("recalling_firm"),
    ]
    source = record.get("source") or {}
    parts.append(source.get("name"))

    return " ".join(str(part).lower() for part in parts if part)


def _should_exclude_for_intent(record: dict[str, Any], intent: FoodRadarSearchIntent) -> bool:
    if not intent.excluded_brand_phrases:
        return False

    search_text = _record_search_text(record)
    return any(phrase in search_text for phrase in intent.excluded_brand_phrases)


def _intent_relevance_score(record: dict[str, Any], intent: FoodRadarSearchIntent) -> int:
    search_text = _record_search_text(record)
    score = 0

    for term in intent.expanded_terms:
        if term and term in search_text:
            score += 20

    if intent.intent_type in {"poultry_meat", "meat", "egg_product"}:
        if record.get("source_type") == "USDA_FSIS_RECALL":
            score += 30
        if any(term in search_text for term in ("poultry", "chicken", "turkey", "beef", "pork", "egg")):
            score += 15

    if intent.intent_type == "supplement":
        if record.get("source_type") == "FDA_FOOD_ENFORCEMENT":
            score += 20
        if any(term in search_text for term in ("supplement", "protein", "whey", "powder", "vitamin")):
            score += 15

    if intent.intent_type == "brand":
        if intent.normalized_query in search_text:
            score += 50

    if record.get("risk_score"):
        score += min(int(record["risk_score"].get("score", 0) / 10), 10)

    return score


def _rank_and_filter_results(
    *,
    records: list[dict[str, Any]],
    intent: FoodRadarSearchIntent,
    limit: int,
) -> list[dict[str, Any]]:
    filtered_records = [
        record
        for record in records
        if not _should_exclude_for_intent(record, intent)
    ]

    return sorted(
        filtered_records,
        key=lambda record: _intent_relevance_score(record, intent),
        reverse=True,
    )[:limit]


async def execute_everyday_safety_search(
    *,
    category: str,
    query: str,
    limit: int,
    request_id: str | None,
) -> dict[str, Any]:
    if category != "food_supplement":
        raise ValueError("Only category=food_supplement is implemented in v0.1.")

    intent = classify_foodradar_search_intent(query)
    search_strategy_used = intent.search_strategy_used

    try:
        fda_payload = await food_client.search_food_recalls(
            query=query,
            limit=limit,
            request_id=request_id,
        )

        fsis_error_message = None
        try:
            fsis_payload = await fsis_client.search_recalls(
                query=query,
                limit=limit,
                request_id=request_id,
            )
        except Exception as exc:
            fsis_error_message = str(exc)
            fsis_payload = {
                "source_id": USDA_FSIS_RECALL["source_id"],
                "source_name": USDA_FSIS_RECALL["source_name"],
                "endpoint": USDA_FSIS_RECALL["endpoint"],
                "query": query,
                "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                "raw": {"results": [], "error": fsis_error_message},
                "records": [],
                "upstream_status": "error",
            }

        fda_raw_results = fda_payload["raw"].get("results", [])
        fsis_raw_results = fsis_payload.get("records", [])

        normalized_results: list[dict[str, Any]] = []

        for index, record in enumerate(fda_raw_results):
            normalized_results.append(
                _normalize_fda_record(
                    record=record,
                    index=index,
                    payload=fda_payload,
                    search_strategy_used=search_strategy_used,
                )
            )

        for index, record in enumerate(fsis_raw_results):
            normalized_results.append(
                _normalize_fsis_record(
                    record=record,
                    index=index,
                    payload=fsis_payload,
                    search_strategy_used=search_strategy_used,
                )
            )

        normalized_results = _rank_and_filter_results(
            records=normalized_results,
            intent=intent,
            limit=limit,
        )
        upstream_status = "empty" if not normalized_results else "success"

        sources_checked = [
            _checked_source(
                payload=fda_payload,
                source_type="FDA_FOOD_ENFORCEMENT",
                record_count=len(fda_raw_results),
            ),
            _checked_source(
                payload=fsis_payload,
                source_type="USDA_FSIS_RECALL",
                record_count=len(fsis_raw_results),
            ),
        ]

        retrieval_timestamp = datetime.now(timezone.utc).isoformat()

        audit_event = build_audit_event(
            module="FoodRadar",
            source_id="foodradar_multi_source",
            source_name="FoodRadar multi-source search",
            endpoint="openFDA Food Enforcement + USDA FSIS Recall API",
            query=query,
            query_params={
                "category": category,
                "q": query,
                "limit": limit,
                "sources_checked": [
                    OPENFDA_FOOD_ENFORCEMENT["source_id"],
                    USDA_FSIS_RECALL["source_id"],
                ],
                "search_strategy_used": search_strategy_used,
                "intent_type": intent.intent_type,
                "primary_source_hint": intent.primary_source_hint,
                "excluded_brand_phrases": intent.excluded_brand_phrases,
            },
            retrieval_timestamp=retrieval_timestamp,
            upstream_status=upstream_status,
            record_count=len(normalized_results),
            transform_version="everyday-safety-food-transform-v0.2",
            score_version="recall-risk-v0.1",
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload={
                "openfda_food_enforcement": fda_payload.get("raw", {}),
                "usda_fsis_recall": fsis_payload.get("raw", {}),
            },
            request_id=request_id,
        )

        return {
            "query": query,
            "category": "food_supplement",
            "category_label": "Food & Supplements",
            "count": len(normalized_results),
            "limit": limit,
            "source_name": "FoodRadar multi-source search",
            "endpoint": "openFDA Food Enforcement + USDA FSIS Recall API",
            "retrieval_timestamp": retrieval_timestamp,
            "score_version": "recall-risk-v0.1",
            "search_strategy_used": search_strategy_used,
            "sources_checked": sources_checked,
            "public_data_disclaimer": (
                "DAV AI provides public-data safety intelligence only. "
                "Food, supplement, meat, poultry, and egg-product recall records should be verified "
                "against official FDA/openFDA and USDA FSIS sources. This is not medical advice, "
                "diagnosis, treatment guidance, or a substitute for official recall instructions."
            ),
            "limitations": [
                "openFDA Food Enforcement covers FDA-regulated food, supplement, grocery, and packaged-food enforcement records.",
                "USDA FSIS Recall API covers meat, poultry, and egg-product recalls and public health alerts.",
                "If one public source is temporarily unavailable, DAV AI may return partial results from the available source and mark the unavailable source as error.",
                "Search results depend on product descriptions, recalling firm names, recall reason text, and source-specific metadata.",
                "Users should verify exact product names, lot numbers, establishment numbers, package sizes, and official FDA/USDA recall notices before taking action.",
            ],
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
        _persist_food_error_audit(
            query=query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
