from datetime import datetime, timezone
import re
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring import RECALL_REVIEW_SCORE_VERSION
from app.scoring.recall_score import calculate_recall_risk_score
from app.services.foodradar_query_normalization import normalize_foodradar_query
from app.services.foodradar_search_intent import FoodRadarSearchIntent, classify_foodradar_search_intent
from app.services.official_public_notice_search import (
    official_notice_source_metadata,
    search_official_public_notices,
)
from app.services.openfda_food_enforcement_client import OpenFDAFoodEnforcementClient
from app.services.usda_fsis_recall_client import USDAFSISRecallClient
from app.sources.registry import (
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    OPENFDA_FOOD_ENFORCEMENT,
    USDA_FSIS_RECALL,
)

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
    raw_query: str,
    limit: int,
    error_message: str,
    request_id: str | None,
):
    query_params = {
        "category": "food_supplement",
        "q": query,
        "limit": limit,
    }
    if raw_query.strip().lower() != query.lower():
        query_params.update(
            {
                "raw_query": raw_query,
                "normalized_query": query,
                "correction_applied": True,
            }
        )

    audit_event = build_audit_event(
        module="FoodRadar",
        source_id="foodradar_multi_source",
        source_name="FoodRadar multi-source search",
        endpoint="FDA public notices + openFDA Food Enforcement + USDA FSIS Recall API",
        query=query,
        query_params=query_params,
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        upstream_status="error",
        record_count=0,
        transform_version="everyday-safety-food-transform-v0.2",
        score_version=RECALL_REVIEW_SCORE_VERSION,
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
        "source_kind": "structured_api",
        "source_record_type": "official API record",
        "title": None,
        "product_name": record.get("product_description"),
        "brand_name": None,
        "company_name": record.get("recalling_firm"),
        "remedy": None,
        "official_url": payload["endpoint"],
        "affected_models": [],
        "affected_lots": [],
        "extraction_confidence": None,
        "source_text_excerpt": None,
        "search_strategy_used": search_strategy_used,
        "risk_score": risk,
        "source": {
            "name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "source_kind": "structured_api",
            "source_type": "official API record",
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
        "source_kind": "structured_api",
        "source_record_type": "official API record",
        "title": _get_first_value(
            record,
            ("title", "recall_title", "field_title"),
        ),
        "product_name": product_description,
        "brand_name": None,
        "company_name": _get_first_value(
            record,
            (
                "field_establishment",
                "establishment",
                "field_company",
                "company",
                "recalling_firm",
            ),
        ),
        "remedy": None,
        "official_url": payload["endpoint"],
        "affected_models": [],
        "affected_lots": [],
        "extraction_confidence": None,
        "source_text_excerpt": None,
        "search_strategy_used": search_strategy_used,
        "risk_score": risk,
        "source": {
            "name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "source_kind": "structured_api",
            "source_type": "official API record",
        },
    }


def _normalize_public_notice_record(
    *,
    record,
    index: int,
    search_strategy_used: str,
) -> dict[str, Any]:
    published_date = record.published_date
    risk = calculate_recall_risk_score(
        {
            "classification": None,
            "status": None,
            "recall_initiation_date": published_date,
            "distribution_pattern": "",
        }
    )
    product_description = record.product_name or record.title

    return {
        "record_id": record.raw_payload_hash or f"fda-notice-{index}",
        "recall_number": record.recall_number,
        "product_description": product_description,
        "reason_for_recall": record.reason or record.hazard_type,
        "classification": None,
        "status": None,
        "recall_initiation_date": published_date,
        "report_date": published_date,
        "distribution_pattern": None,
        "recalling_firm": record.company_name,
        "product_quantity": None,
        "code_info": ", ".join(record.affected_lots) or None,
        "source_type": (
            "FDA_NORMALIZED_PUBLIC_NOTICE"
            if record.source_kind == "normalized_public_notice"
            else "FDA_PUBLIC_NOTICE"
        ),
        "source_kind": record.source_kind,
        "source_record_type": record.source_type,
        "title": record.title,
        "product_name": record.product_name,
        "brand_name": record.brand_name,
        "company_name": record.company_name,
        "remedy": record.remedy,
        "official_url": record.record_url,
        "affected_models": record.affected_models,
        "affected_lots": record.affected_lots,
        "extraction_confidence": record.extraction_confidence,
        "source_text_excerpt": record.source_text_excerpt,
        "search_strategy_used": search_strategy_used,
        "risk_score": risk,
        "source": {
            "name": record.source_name,
            "endpoint": record.record_url or record.source_url,
            "retrieval_timestamp": record.retrieved_at,
            "source_kind": record.source_kind,
            "source_type": record.source_type,
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
        record.get("title"),
        record.get("product_name"),
        record.get("brand_name"),
        record.get("company_name"),
        record.get("remedy"),
        record.get("source_text_excerpt"),
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


def _date_sort_value(record: dict[str, Any]) -> int:
    for key in ("report_date", "recall_initiation_date"):
        value = record.get(key)
        if value in (None, ""):
            continue

        text = str(value).strip()

        # openFDA commonly uses YYYYMMDD.
        digits = "".join(character for character in text if character.isdigit())
        if len(digits) == 8 and text[:4].isdigit():
            return int(digits)

        # FDA public notice pages commonly use MM/DD/YYYY.
        match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
        if match:
            month, day, year = match.groups()
            return int(f"{year}{int(month):02d}{int(day):02d}")

        if len(digits) >= 8:
            return int(digits[:8])

    return 0


def _rank_and_filter_results(
    *,
    records: list[dict[str, Any]],
    intent: FoodRadarSearchIntent,
    limit: int,
    sort: str,
) -> list[dict[str, Any]]:
    filtered_records = [
        record
        for record in records
        if not _should_exclude_for_intent(record, intent)
    ]

    if sort == "latest":
        return sorted(
            filtered_records,
            key=lambda record: (
                _date_sort_value(record),
                _intent_relevance_score(record, intent),
                record.get("risk_score", {}).get("score", 0),
            ),
            reverse=True,
        )[:limit]

    return sorted(
        filtered_records,
        key=lambda record: (
            _intent_relevance_score(record, intent),
            record.get("risk_score", {}).get("score", 0),
            _date_sort_value(record),
        ),
        reverse=True,
    )[:limit]


async def execute_everyday_safety_search(
    *,
    category: str,
    query: str,
    limit: int,
    sort: str = "score",
    request_id: str | None = None,
) -> dict[str, Any]:
    if category != "food_supplement":
        raise ValueError("Only category=food_supplement is implemented in v0.1.")

    query_normalization = normalize_foodradar_query(query)
    search_query = query_normalization.normalized_query
    if not search_query:
        raise ValueError("FoodRadar search query must contain at least two non-whitespace characters.")

    intent = classify_foodradar_search_intent(search_query)
    search_strategy_used = intent.search_strategy_used

    try:
        fda_payload = await food_client.search_food_recalls(
            query=search_query,
            limit=25,
            request_id=request_id,
        )

        fsis_error_message = None
        try:
            fsis_payload = await fsis_client.search_recalls(
                query=search_query,
                limit=25,
                request_id=request_id,
            )
        except Exception as exc:
            fsis_error_message = str(exc)
            fsis_payload = {
                "source_id": USDA_FSIS_RECALL["source_id"],
                "source_name": USDA_FSIS_RECALL["source_name"],
                "endpoint": USDA_FSIS_RECALL["endpoint"],
                "query": search_query,
                "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                "raw": {"results": [], "error": fsis_error_message},
                "records": [],
                "upstream_status": "error",
            }

        notice_error_message = None
        try:
            notice_result = await search_official_public_notices(
                query=search_query,
                limit=25,
                request_id=request_id,
                domain="food",
            )
        except Exception as exc:
            notice_error_message = str(exc)
            notice_result = None

        fda_raw_results = fda_payload["raw"].get("results", [])
        fsis_raw_results = fsis_payload.get("records", [])
        notice_records = notice_result.records if notice_result else []

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

        for index, record in enumerate(notice_records):
            normalized_results.append(
                _normalize_public_notice_record(
                    record=record,
                    index=index,
                    search_strategy_used=search_strategy_used,
                )
            )

        normalized_results = _rank_and_filter_results(
            records=normalized_results,
            intent=intent,
            limit=limit,
            sort=sort,
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
        if notice_result:
            sources_checked.append(official_notice_source_metadata(notice_result))
        else:
            sources_checked.append(
                {
                    "source_id": FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
                    "source_name": FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_name"],
                    "source_type": "FDA_PUBLIC_NOTICE",
                    "endpoint": FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["endpoint"],
                    "source_kind": "public_notice",
                    "record_type": "public notice page",
                    "upstream_status": "error",
                    "record_count": 0,
                }
            )

        retrieval_timestamp = datetime.now(timezone.utc).isoformat()

        audit_event = build_audit_event(
            module="FoodRadar",
            source_id="foodradar_multi_source",
            source_name="FoodRadar multi-source search",
            endpoint="FDA public notices + openFDA Food Enforcement + USDA FSIS Recall API",
            query=search_query,
            query_params={
                "category": category,
                "q": search_query,
                "raw_query": query_normalization.raw_query,
                "normalized_query": query_normalization.normalized_query,
                "correction_applied": query_normalization.correction_applied,
                "limit": limit,
                "sort": sort,
                "upstream_fetch_limit": 25,
                "sources_checked": [
                    OPENFDA_FOOD_ENFORCEMENT["source_id"],
                    USDA_FSIS_RECALL["source_id"],
                    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
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
            score_version=RECALL_REVIEW_SCORE_VERSION,
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        source_pull_result = _save_source_pull_with_request_id(
            audit_event=audit_event,
            raw_payload={
                "openfda_food_enforcement": fda_payload.get("raw", {}),
                "usda_fsis_recall": fsis_payload.get("raw", {}),
                "fda_public_notices": notice_result.raw_payload if notice_result else {
                    "error": notice_error_message,
                },
            },
            request_id=request_id,
        )

        return {
            "query": search_query,
            "raw_query": query_normalization.raw_query,
            "normalized_query": query_normalization.normalized_query,
            "correction_applied": query_normalization.correction_applied,
            "suggestion_message": query_normalization.suggestion_message,
            "category": "food_supplement",
            "category_label": "Food & Supplements",
            "count": len(normalized_results),
            "limit": limit,
            "source_name": "FoodRadar multi-source search",
            "endpoint": "FDA public notices + openFDA Food Enforcement + USDA FSIS Recall API",
            "retrieval_timestamp": retrieval_timestamp,
            "score_version": RECALL_REVIEW_SCORE_VERSION,
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
                "FDA public recall and safety notice pages are matched against concise normalized fields and official notice text.",
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
            query=search_query,
            raw_query=query_normalization.raw_query,
            limit=limit,
            error_message=str(exc),
            request_id=request_id,
        )
        raise
