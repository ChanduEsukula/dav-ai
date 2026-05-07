from collections import Counter

from fastapi import APIRouter, HTTPException, Query, Request

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.schemas.drug_events import DrugEventSearchResponse
from app.services.openfda_drug_event_client import OpenFDADrugEventClient

router = APIRouter()
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


@router.get("/search", response_model=DrugEventSearchResponse)
async def search_drug_events(
    request: Request,
    q: str = Query(..., min_length=2, description="Drug name or medicinal product"),
    limit: int = Query(10, ge=1, le=25),
):
    try:
        request_id = getattr(request.state, "request_id", None)
        payload = await _search_drug_events_with_request_id(query=q, limit=limit, request_id=request_id)
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

        audit_event = build_audit_event(
            module="DrugSignal",
            source_id=payload["source_id"],
            source_name=payload["source_name"],
            endpoint=payload["endpoint"],
            query=q,
            query_params={"q": q, "limit": limit},
            retrieval_timestamp=payload["retrieval_timestamp"],
            upstream_status=upstream_status,
            record_count=len(raw_results),
            transform_version="drug-event-transform-v0.1",
        )

        _save_audit_event_with_request_id(audit_event, request_id=request_id)

        return {
            "query": q,
            "count": len(raw_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "medical_disclaimer": "MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "faers_disclaimer": "FAERS adverse-event reports do not prove that a drug caused a reaction. Reports may be incomplete, duplicated, or influenced by reporting patterns.",
            "audit": {
                "audit_id": audit_event["audit_id"],
                "source_id": audit_event["source_id"],
                "module": audit_event["module"],
                "upstream_status": audit_event["upstream_status"],
                "record_count": audit_event["record_count"],
                "transform_version": audit_event["transform_version"],
            },
            "top_reactions": top_reactions,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve drug event data from openFDA.",
                "error": str(exc),
            },
        )