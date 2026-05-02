from fastapi import APIRouter

from app.schemas.sources import SourceRegistryResponse
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT, OPENFDA_DRUG_EVENT

router = APIRouter()


@router.get("", response_model=SourceRegistryResponse)
async def list_sources():
    sources = [
        OPENFDA_DRUG_ENFORCEMENT,
        OPENFDA_DRUG_EVENT,
    ]

    return {
        "count": len(sources),
        "sources": sources,
    }