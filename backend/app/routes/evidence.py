from fastapi import APIRouter, HTTPException
from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable
from app.services.pharma.evidence import drug_evidence, release_metadata

router = APIRouter(tags=["Pharmaceutical evidence"])


@router.get("/api/coverage")
def coverage():
    try:
        return release_metadata()
    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(503, "Pharmaceutical release is unavailable") from exc


@router.get("/api/drugs/{product_id}/evidence")
def evidence(product_id: str):
    try:
        result = drug_evidence(product_id)
    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(503, "Pharmaceutical release is unavailable") from exc
    if result is None:
        raise HTTPException(404, "Drug not found")
    return result
