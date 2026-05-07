from fastapi import APIRouter

from app.db.audit_repository import list_audit_events
from app.db.database import is_database_configured
from app.schemas.system import SystemStatusResponse
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT, OPENFDA_DRUG_EVENT

router = APIRouter(prefix="/api/v1/system")


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status() -> SystemStatusResponse:
    sources = [
        OPENFDA_DRUG_ENFORCEMENT,
        OPENFDA_DRUG_EVENT,
    ]

    database_configured = is_database_configured()
    audit_readable = False

    if database_configured:
        persistence_status, _ = list_audit_events(limit=1)
        audit_readable = persistence_status == "saved"

    return SystemStatusResponse(
        status="ok",
        app="MedTrek AI API",
        version="0.1.0",
        database={
            "configured": database_configured,
            "audit_readable": audit_readable,
        },
        sources={
            "registered_count": len(sources),
            "available": len(sources) > 0,
        },
        modules=[
            "RecallRadar",
            "DrugSignal",
            "Sources",
            "Audit History",
        ],
    )
