from fastapi import APIRouter, HTTPException, Query, Request

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.schemas.recalls import RecallSearchResponse
from app.scoring.recall_score import calculate_recall_risk_score
from app.services.openfda_client import OpenFDAClient

router = APIRouter()
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


@router.get("/search", response_model=RecallSearchResponse)
async def search_recalls(
    request: Request,
    q: str = Query(..., min_length=2, description="Drug, product, brand, or recall keyword"),
    limit: int = Query(10, ge=1, le=25),
):
    try:
        request_id = getattr(request.state, "request_id", None)
        payload = await _search_drug_recalls_with_request_id(query=q, limit=limit, request_id=request_id)
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
            query=q,
            query_params={"q": q, "limit": limit},
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(normalized_results),
            transform_version="recall-transform-v0.1",
            score_version="recall-risk-v0.1",
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        return {
            "query": q,
            "count": len(normalized_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "score_version": "recall-risk-v0.1",
            "medical_disclaimer": "MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "audit": {
                "audit_id": audit_event["audit_id"],
                "source_id": audit_event["source_id"],
                "module": audit_event["module"],
                "upstream_status": audit_event["upstream_status"],
                "record_count": audit_event["record_count"],
                "transform_version": audit_event["transform_version"],
            },
            "results": normalized_results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve recall data from openFDA.",
                "error": str(exc),
            },
        )