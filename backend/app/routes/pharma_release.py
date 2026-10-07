import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/v1/pharma/releases",
    tags=["Pharma Release"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SEMAGLUTIDE_SNAPSHOT = (
    PROJECT_ROOT
    / "data"
    / "releases"
    / "dav_ai_v1"
    / "semaglutide"
    / "semaglutide_snapshot.json"
)


@lru_cache(maxsize=1)
def load_semaglutide_snapshot() -> dict:
    if not SEMAGLUTIDE_SNAPSHOT.exists():
        raise FileNotFoundError(
            f"Semaglutide snapshot not found: {SEMAGLUTIDE_SNAPSHOT}"
        )

    with SEMAGLUTIDE_SNAPSHOT.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


@router.get("/semaglutide")
def get_semaglutide_release():
    try:
        return load_semaglutide_snapshot()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Semaglutide release artifact is unavailable.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Semaglutide release artifact is invalid.",
        ) from exc
