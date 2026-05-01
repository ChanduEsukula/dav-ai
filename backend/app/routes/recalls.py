from fastapi import APIRouter, HTTPException, Query
from app.schemas.recalls import RecallSearchResponse
from app.services.openfda_client import OpenFDAClient
from app.scoring.recall_score import calculate_recall_risk_score

router = APIRouter()
client = OpenFDAClient()


@router.get("/search", response_model=RecallSearchResponse)
async def search_recalls(
    q: str = Query(..., min_length=2, description="Drug, product, brand, or recall keyword"),
    limit: int = Query(10, ge=1, le=25),
):
    try:
        payload = await client.search_drug_recalls(query=q, limit=limit)
        raw_results = payload["raw"].get("results", [])

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

        return {
            "query": q,
            "count": len(normalized_results),
            "limit": limit,
            "source_name": payload["source_name"],
            "retrieval_timestamp": payload["retrieval_timestamp"],
            "medical_disclaimer": "MedSignal AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.",
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
