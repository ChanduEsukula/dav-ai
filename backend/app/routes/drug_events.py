from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from app.schemas.drug_events import DrugEventSearchResponse
from app.services.openfda_drug_event_client import OpenFDADrugEventClient

router = APIRouter()
client = OpenFDADrugEventClient()


@router.get("/search", response_model=DrugEventSearchResponse)
async def search_drug_events(
    q: str = Query(..., min_length=2, description="Drug name or medicinal product"),
    limit: int = Query(10, ge=1, le=25),
):
    try:
        payload = await client.search_drug_events(query=q, limit=limit)
        raw_results = payload["raw"].get("results", [])

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

        return {
            "query": q,
            "count": len(raw_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "endpoint": payload["endpoint"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "medical_disclaimer": "MedSignal AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
            "faers_disclaimer": "FAERS adverse-event reports do not prove that a drug caused a reaction. Reports may be incomplete, duplicated, or influenced by reporting patterns.",
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