from fastapi import APIRouter, HTTPException, Query
from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable
from app.schemas.medication_overview import MedicationOverview, DataInventory
from app.services.pharma.medication_overview import medication_overview, data_inventory

router = APIRouter(tags=['Medication discovery'])

@router.get('/api/medications/overview', response_model=MedicationOverview)
def overview(q: str = Query(min_length=1, max_length=200)):
    if not q.strip():
        raise HTTPException(422, 'Query must not be blank')
    try:
        return medication_overview(q)
    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(503, 'Pharmaceutical release is unavailable') from exc

@router.get('/api/coverage/inventory', response_model=DataInventory)
def inventory():
    try:
        return data_inventory()
    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(503, 'Pharmaceutical release is unavailable') from exc
