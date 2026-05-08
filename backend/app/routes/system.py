from fastapi import APIRouter

from app.db.audit_repository import list_audit_events
from app.db.database import is_database_configured
from app.schemas.system import DataQualityResponse, SystemStatusResponse
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT, OPENFDA_DRUG_EVENT

router = APIRouter(prefix="/api/v1/system")


def get_registered_sources() -> list[dict[str, str]]:
    return [
        OPENFDA_DRUG_ENFORCEMENT,
        OPENFDA_DRUG_EVENT,
    ]


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status() -> SystemStatusResponse:
    sources = get_registered_sources()

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


@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality() -> DataQualityResponse:
    sources = get_registered_sources()
    database_configured = is_database_configured()

    if not database_configured:
        return DataQualityResponse(
            status="skipped",
            database_configured=False,
            audit_readable=False,
            source_registry_count=len(sources),
            recent_audit_count=0,
            upstream_status_counts={
                "success": 0,
                "empty": 0,
                "error": 0,
            },
            latest_audit_event={
                "exists": False,
            },
        )

    persistence_status, rows = list_audit_events(limit=25)
    audit_readable = persistence_status == "saved"

    if not audit_readable:
        return DataQualityResponse(
            status=persistence_status,
            database_configured=True,
            audit_readable=False,
            source_registry_count=len(sources),
            recent_audit_count=0,
            upstream_status_counts={
                "success": 0,
                "empty": 0,
                "error": 0,
            },
            latest_audit_event={
                "exists": False,
            },
        )

    status_counts = {
        "success": 0,
        "empty": 0,
        "error": 0,
    }

    for row in rows:
        upstream_status = row.get("upstream_status")
        if upstream_status in status_counts:
            status_counts[upstream_status] += 1

    latest_row = rows[0] if rows else None

    latest_audit_event = {
        "exists": latest_row is not None,
    }

    if latest_row:
        latest_audit_event.update(
            {
                "audit_id": latest_row.get("audit_id"),
                "module": latest_row.get("module"),
                "query": latest_row.get("query"),
                "upstream_status": latest_row.get("upstream_status"),
                "record_count": latest_row.get("record_count"),
                "created_at": str(latest_row.get("created_at")) if latest_row.get("created_at") else None,
            }
        )

    return DataQualityResponse(
        status="ok",
        database_configured=True,
        audit_readable=True,
        source_registry_count=len(sources),
        recent_audit_count=len(rows),
        upstream_status_counts=status_counts,
        latest_audit_event=latest_audit_event,
    )
