from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SourceAdapterResult,
    date_sort_value,
    match_score,
    utc_now_iso,
)
from app.services.safety_source_adapters.cpsc import CPSCRecallsAdapter
from app.services.safety_source_adapters.fda_public import FDAPublicRecallsAdapter
from app.services.safety_source_adapters.openfda_food import OpenFDAFoodEnforcementAdapter
from app.services.safety_source_adapters.openfda_drug import OpenFDADrugEnforcementAdapter
from app.services.safety_source_adapters.rxnorm import RxNormDrugReferenceAdapter
from app.services.safety_source_adapters.usda_fsis import USDAFSISRecallAdapter
from app.services.safety_source_adapters.dailymed import DailyMedSPLAdapter
from app.services.safety_source_adapters.openfda_drug_label import OpenFDADrugLabelAdapter
from app.services.safety_source_adapters.openfda_ndc import OpenFDANDCDirectoryAdapter
from app.services.safety_source_adapters.openfda_device import OpenFDADeviceEnforcementAdapter
from app.services.safety_source_adapters.openfda_device_event import OpenFDADeviceEventAdapter
from app.services.search_workflows.real_world_query_understanding import understand_real_world_safety_query
from app.services.search_workflows.safety_intelligence_summary import build_safety_intelligence_summary
from app.services.safety_source_adapters.nhtsa import (
    NHTSARecallsAdapter,
    NHTSAVPICAdapter,
    VehicleIdentity,
    is_vin_like,
    parse_vehicle_query,
)
from app.sources.registry import (
    CPSC_RECALLS_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    OPENFDA_FOOD_ENFORCEMENT,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_NDC_DIRECTORY,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
    DAILYMED_SPL_API,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    NHTSA_RECALLS_API_DATASETS,
    NHTSA_VPIC_VIN_DECODER_API,
)


NO_MATCH_EXPLANATION = (
    "No matching public record was found in the checked U.S. sources. "
    "This does not certify that the product is safe."
)
REAL_WORLD_SAFETY_TRANSFORM_VERSION = "real-world-safety-v1"
SOURCE_TIMEOUT_SECONDS = 5.0
PUBLIC_DATA_DISCLAIMER = (
    "Dav AI checks selected U.S. public recall and safety-notice sources only. "
    "Results are informational and should be verified against the official source pages."
)
LIMITATIONS = [
    "Version 1 checks CPSC consumer product recalls, curated official openFDA Food Enforcement records, curated official openFDA Drug Enforcement records, RxNorm/RxNav drug-name reference records, DailyMed official SPL drug label records, openFDA NDC Directory drug identity/reference records, openFDA medical device enforcement records, openFDA medical device adverse-event reports, NHTSA vehicle recalls for VIN or make/model/year input, and the FDA public recalls page.",
    "No matching public record was found in the checked U.S. sources. This does not certify that the product is safe.",
    "Search results depend on source-provided product names, company names, campaign metadata, recall descriptions, and public notice table text.",
    "If one source is temporarily unavailable, Dav AI returns partial results from remaining checked sources and lists the failed source.",
    "This is not medical advice, legal advice, a drug interaction checker, ingredient scoring, or a replacement for official recall instructions.",
]

cpsc_adapter = CPSCRecallsAdapter()
fda_public_adapter = FDAPublicRecallsAdapter()
openfda_food_adapter = OpenFDAFoodEnforcementAdapter()
usda_fsis_adapter = USDAFSISRecallAdapter()
openfda_drug_adapter = OpenFDADrugEnforcementAdapter()
rxnorm_adapter = RxNormDrugReferenceAdapter()
dailymed_adapter = DailyMedSPLAdapter()
openfda_drug_label_adapter = OpenFDADrugLabelAdapter()
openfda_ndc_adapter = OpenFDANDCDirectoryAdapter()
openfda_device_adapter = OpenFDADeviceEnforcementAdapter()
openfda_device_event_adapter = OpenFDADeviceEventAdapter()
vpic_adapter = NHTSAVPICAdapter()
nhtsa_recalls_adapter = NHTSARecallsAdapter()
logger = logging.getLogger("dav_ai.real_world_safety.workflow")


def _save_audit_event_with_request_id(audit_event: dict[str, Any], request_id: str | None):
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


def _checked_source(result: SourceAdapterResult) -> dict[str, Any]:
    return {
        "source_id": result.source_id,
        "source_name": result.source_name,
        "source_type": result.source_type,
        "source_url": result.source_url,
        "source_kind": result.source_kind,
        "upstream_status": result.upstream_status,
        "record_count": len(result.records),
    }


def _failed_source(
    *,
    source: dict[str, str],
    source_type: str,
    source_kind: str,
    error_type: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "source_type": source_type,
        "source_url": source["endpoint"],
        "source_kind": source_kind,
        "error_type": error_type,
        "reason": reason,
    }


def _persist_source_result(
    *,
    result: SourceAdapterResult,
    query: str,
    raw_query: str,
    limit: int,
    sort: str,
    request_id: str | None,
) -> dict[str, Any]:
    audit_event = build_audit_event(
        module="RealWorldSafety",
        source_id=result.source_id,
        source_name=result.source_name,
        endpoint=result.source_url,
        query=query,
        query_params={
            "q": query,
            "raw_query": raw_query,
            "limit": limit,
            "sort": sort,
            "source_type": result.source_type,
            "source_kind": result.source_kind,
            "context": result.context,
        },
        retrieval_timestamp=result.retrieved_at,
        upstream_status=result.upstream_status,
        record_count=len(result.records),
        transform_version=REAL_WORLD_SAFETY_TRANSFORM_VERSION,
        score_version=None,
        error_message=result.error_message,
    )

    _save_audit_event_with_request_id(audit_event, request_id=request_id)
    source_pull_result = _save_source_pull_with_request_id(
        audit_event=audit_event,
        raw_payload=result.raw_payload,
        request_id=request_id,
    )

    return {
        "audit_id": audit_event["audit_id"],
        "source_id": audit_event["source_id"],
        "source_name": audit_event["source_name"],
        "module": audit_event["module"],
        "upstream_status": audit_event["upstream_status"],
        "record_count": audit_event["record_count"],
        "transform_version": audit_event["transform_version"],
        "source_snapshot_status": source_pull_result["status"],
        "source_pull_id": source_pull_result["pull_id"],
        "source_payload_hash": source_pull_result["payload_hash"],
    }


def _persist_source_error(
    *,
    source: dict[str, str],
    source_type: str,
    source_kind: str,
    query: str,
    raw_query: str,
    limit: int,
    sort: str,
    error_type: str,
    error_message: str,
    request_id: str | None,
) -> dict[str, Any]:
    retrieval_timestamp = utc_now_iso()
    audit_event = build_audit_event(
        module="RealWorldSafety",
        source_id=source["source_id"],
        source_name=source["source_name"],
        endpoint=source["endpoint"],
        query=query,
        query_params={
            "q": query,
            "raw_query": raw_query,
            "limit": limit,
            "sort": sort,
            "source_type": source_type,
            "source_kind": source_kind,
            "error_type": error_type,
        },
        retrieval_timestamp=retrieval_timestamp,
        upstream_status="error",
        record_count=0,
        transform_version=REAL_WORLD_SAFETY_TRANSFORM_VERSION,
        score_version=None,
        error_message=error_message,
    )

    _save_audit_event_with_request_id(audit_event, request_id=request_id)
    source_pull_result = _save_source_pull_with_request_id(
        audit_event=audit_event,
        raw_payload={"error": error_message, "error_type": error_type},
        request_id=request_id,
    )

    return {
        "audit_id": audit_event["audit_id"],
        "source_id": audit_event["source_id"],
        "source_name": audit_event["source_name"],
        "module": audit_event["module"],
        "upstream_status": audit_event["upstream_status"],
        "record_count": audit_event["record_count"],
        "transform_version": audit_event["transform_version"],
        "source_snapshot_status": source_pull_result["status"],
        "source_pull_id": source_pull_result["pull_id"],
        "source_payload_hash": source_pull_result["payload_hash"],
    }


async def _run_adapter_call(
    *,
    adapter_call,
    source: dict[str, str],
    source_type: str,
    source_kind: str,
    query: str,
    raw_query: str,
    limit: int,
    sort: str,
    request_id: str | None,
    results: list[NormalizedSafetyRecord],
    sources_checked: list[dict[str, Any]],
    sources_failed: list[dict[str, Any]],
    source_audits: list[dict[str, Any]],
) -> SourceAdapterResult | None:
    started_at = time.perf_counter()
    logger.info(
        "real_world_safety_source_started",
        extra={
            "event": "real_world_safety_source_started",
            "request_id": request_id,
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "query": query,
            "timeout_seconds": SOURCE_TIMEOUT_SECONDS,
        },
    )

    try:
        result = await asyncio.wait_for(
            adapter_call(),
            timeout=SOURCE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        error_type = "timeout"
        error_message = f"Timed out after {SOURCE_TIMEOUT_SECONDS} seconds checking {source['source_name']}."
        logger.warning(
            "real_world_safety_source_timed_out",
            extra={
                "event": "real_world_safety_source_timed_out",
                "request_id": request_id,
                "source_id": source["source_id"],
                "source_name": source["source_name"],
                "query": query,
                "duration_ms": duration_ms,
                "timeout_seconds": SOURCE_TIMEOUT_SECONDS,
            },
        )
        sources_failed.append(
            _failed_source(
                source=source,
                source_type=source_type,
                source_kind=source_kind,
                error_type=error_type,
                reason=error_message,
            )
        )
        source_audits.append(
            _persist_source_error(
                source=source,
                source_type=source_type,
                source_kind=source_kind,
                query=query,
                raw_query=raw_query,
                limit=limit,
                sort=sort,
                error_type=error_type,
                error_message=error_message,
                request_id=request_id,
            )
        )
        return None
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        error_type = getattr(exc, "error_type", exc.__class__.__name__)
        error_message = str(exc) or f"{source['source_name']} failed with {error_type}."
        logger.warning(
            "real_world_safety_source_failed",
            extra={
                "event": "real_world_safety_source_failed",
                "request_id": request_id,
                "source_id": source["source_id"],
                "source_name": source["source_name"],
                "query": query,
                "duration_ms": duration_ms,
                "error_type": error_type,
            },
        )
        sources_failed.append(
            _failed_source(
                source=source,
                source_type=source_type,
                source_kind=source_kind,
                error_type=error_type,
                reason=error_message,
            )
        )
        source_audits.append(
            _persist_source_error(
                source=source,
                source_type=source_type,
                source_kind=source_kind,
                query=query,
                raw_query=raw_query,
                limit=limit,
                sort=sort,
                error_type=error_type,
                error_message=error_message,
                request_id=request_id,
            )
        )
        return None

    sources_checked.append(_checked_source(result))
    results.extend(result.records)
    source_audits.append(
        _persist_source_result(
            result=result,
            query=query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
        )
    )
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "real_world_safety_source_completed",
        extra={
            "event": "real_world_safety_source_completed",
            "request_id": request_id,
            "source_id": result.source_id,
            "source_name": result.source_name,
            "query": query,
            "duration_ms": duration_ms,
            "upstream_status": result.upstream_status,
            "record_count": len(result.records),
        },
    )
    return result


def _rank_results(
    *,
    records: list[NormalizedSafetyRecord],
    query: str,
    limit: int,
    sort: str,
) -> list[NormalizedSafetyRecord]:
    if sort == "latest":
        return sorted(
            records,
            key=lambda record: (
                date_sort_value(record.published_date),
                match_score(record, query),
            ),
            reverse=True,
        )[:limit]

    return sorted(
        records,
        key=lambda record: (
            match_score(record, query),
            date_sort_value(record.published_date),
        ),
        reverse=True,
    )[:limit]


async def execute_real_world_safety_search(
    *,
    query: str,
    limit: int,
    sort: str = "score",
    request_id: str | None = None,
) -> dict[str, Any]:
    raw_query = query
    query_understanding = understand_real_world_safety_query(query)
    search_query = query_understanding.search_query
    response_query = search_query if query_understanding.corrections_applied else " ".join(query.split())
    if not search_query:
        raise ValueError("Real-world safety search query must contain at least two non-whitespace characters.")

    workflow_started_at = time.perf_counter()
    retrieval_timestamp = utc_now_iso()
    records: list[NormalizedSafetyRecord] = []
    sources_checked: list[dict[str, Any]] = []
    sources_failed: list[dict[str, Any]] = []
    source_audits: list[dict[str, Any]] = []

    logger.info(
        "real_world_safety_workflow_started",
        extra={
            "event": "real_world_safety_workflow_started",
            "request_id": request_id,
            "query": search_query,
            "limit": limit,
            "sort": sort,
        },
    )

    vehicle_identity: VehicleIdentity | None = None
    vin = search_query.strip().upper()

    initial_calls = [
        _run_adapter_call(
            adapter_call=lambda: cpsc_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=CPSC_RECALLS_API,
            source_type="API",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: fda_public_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
            source_type="public notice page",
            source_kind="public_notice",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_food_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_FOOD_ENFORCEMENT,
            source_type="local official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: usda_fsis_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=USDA_FSIS_RECALL,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_drug_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_DRUG_ENFORCEMENT,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: rxnorm_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=RXNORM_RXNAV_API,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: dailymed_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=DAILYMED_SPL_API,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_drug_label_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_DRUG_LABEL,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_ndc_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_NDC_DIRECTORY,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_device_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_DEVICE_ENFORCEMENT,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
        _run_adapter_call(
            adapter_call=lambda: openfda_device_event_adapter.search(
                query=search_query,
                limit=limit,
                request_id=request_id,
            ),
            source=OPENFDA_DEVICE_EVENT,
            source_type="local curated official snapshot",
            source_kind="structured_api",
            query=search_query,
            raw_query=raw_query,
            limit=limit,
            sort=sort,
            request_id=request_id,
            results=records,
            sources_checked=sources_checked,
            sources_failed=sources_failed,
            source_audits=source_audits,
        ),
    ]

    if is_vin_like(vin):
        initial_calls.append(
            _run_adapter_call(
                adapter_call=lambda: vpic_adapter.decode(vin=vin, request_id=request_id),
                source=NHTSA_VPIC_VIN_DECODER_API,
                source_type="API",
                source_kind="structured_api",
                query=search_query,
                raw_query=raw_query,
                limit=limit,
                sort=sort,
                request_id=request_id,
                results=records,
                sources_checked=sources_checked,
                sources_failed=sources_failed,
                source_audits=source_audits,
            )
        )
    else:
        vehicle_identity = parse_vehicle_query(search_query)
        if vehicle_identity:
            initial_calls.append(
                _run_adapter_call(
                    adapter_call=lambda: nhtsa_recalls_adapter.search_vehicle_recalls(
                        vehicle=vehicle_identity,
                        limit=limit,
                        request_id=request_id,
                    ),
                    source=NHTSA_RECALLS_API_DATASETS,
                    source_type="API",
                    source_kind="structured_api",
                    query=search_query,
                    raw_query=raw_query,
                    limit=limit,
                    sort=sort,
                    request_id=request_id,
                    results=records,
                    sources_checked=sources_checked,
                    sources_failed=sources_failed,
                    source_audits=source_audits,
                )
            )

    initial_results = await asyncio.gather(*initial_calls)

    if is_vin_like(vin):
        vpic_result = next(
            (
                result
                for result in initial_results
                if result and result.source_id == NHTSA_VPIC_VIN_DECODER_API["source_id"]
            ),
            None,
        )
        if vpic_result and vpic_result.context.get("vehicle_identity"):
            identity_payload = vpic_result.context["vehicle_identity"]
            vehicle_identity = VehicleIdentity(
                make=identity_payload["make"],
                model=identity_payload["model"],
                model_year=identity_payload["model_year"],
                vin=identity_payload.get("vin"),
            )

            await _run_adapter_call(
                adapter_call=lambda: nhtsa_recalls_adapter.search_vehicle_recalls(
                    vehicle=vehicle_identity,
                    limit=limit,
                    request_id=request_id,
                ),
                source=NHTSA_RECALLS_API_DATASETS,
                source_type="API",
                source_kind="structured_api",
                query=search_query,
                raw_query=raw_query,
                limit=limit,
                sort=sort,
                request_id=request_id,
                results=records,
                sources_checked=sources_checked,
                sources_failed=sources_failed,
                source_audits=source_audits,
            )

    records_per_source: dict[str, int] = {}
    for record in records:
        records_per_source[record.source_name] = records_per_source.get(record.source_name, 0) + 1

    structured_api_matches = sum(1 for record in records if record.source_kind == "structured_api")
    public_notice_matches = sum(1 for record in records if record.source_kind == "public_notice")
    total_matches = len(records)
    ranked_records = _rank_results(
        records=records,
        query=vehicle_identity.query_label if vehicle_identity else search_query,
        limit=limit,
        sort=sort,
    )

    safety_intelligence_summary = build_safety_intelligence_summary(
        query=search_query,
        records=records,
        ranked_records=ranked_records,
        sources_checked=sources_checked,
        sources_failed=sources_failed,
    )

    response = {
        "query": response_query,
        "raw_query": raw_query,
        "query_understanding": query_understanding.as_response_dict(),
        "count": len(ranked_records),
        "limit": limit,
        "retrieval_timestamp": retrieval_timestamp,
        "sources_checked": sources_checked,
        "sources_failed": sources_failed,
        "records_per_source": records_per_source,
        "structured_api_matches": structured_api_matches,
        "public_notice_matches": public_notice_matches,
        "total_matches": total_matches,
        "no_match_explanation": NO_MATCH_EXPLANATION if total_matches == 0 else None,
        "safety_intelligence_summary": safety_intelligence_summary,
        "public_data_disclaimer": PUBLIC_DATA_DISCLAIMER,
        "limitations": LIMITATIONS,
        "source_audits": source_audits,
        "results": [record.as_response_dict() for record in ranked_records],
    }

    logger.info(
        "real_world_safety_response_assembled",
        extra={
            "event": "real_world_safety_response_assembled",
            "request_id": request_id,
            "query": search_query,
            "duration_ms": round((time.perf_counter() - workflow_started_at) * 1000, 2),
            "total_matches": total_matches,
            "returned_count": len(ranked_records),
            "sources_checked": len(sources_checked),
            "sources_failed": len(sources_failed),
        },
    )
    return response
