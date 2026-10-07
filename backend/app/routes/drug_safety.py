from typing import Literal

from fastapi import APIRouter, HTTPException

from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository

router = APIRouter(prefix="/api/drugs", tags=["Stored Drug Safety"])


def read(product_id: str, timeline: bool = False):
    try:
        repo = FrozenPharmaReleaseRepository()

        result = (
            repo.timeline(product_id)
            if timeline
            else repo.safety(product_id)
        )

        if result is None:
            raise HTTPException(404, "Drug not found")

        return result

    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(
            503,
            "Stored pharmaceutical safety release is unavailable",
        ) from exc


@router.get("/{product_id}/safety")
def drug_safety(product_id: str):
    return read(product_id)


@router.get("/{product_id}/timeline")
def drug_timeline(product_id: str):
    return read(product_id, timeline=True)


@router.get("/{product_id}/safety/{section}")
def drug_safety_section(
    product_id: str,
    section: Literal[
        "labels",
        "recalls",
        "adverse_events",
        "communications",
    ],
):
    result = read(product_id)
    return {
        "drug_id": product_id,
        **result[section],
    }
