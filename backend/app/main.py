import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.audit_events import router as audit_events_router
from app.routes.drug_events import router as drug_events_router
from app.routes.recalls import router as recalls_router
from app.routes.sources import router as sources_router


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="MedTrek AI API",
    description="Healthcare safety intelligence API for recalls, adverse-event signals, source transparency, and audit-aware safety briefings.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recalls_router, prefix="/api/v1/recalls", tags=["RecallRadar"])
app.include_router(drug_events_router, prefix="/api/v1/drug-events", tags=["DrugSignal"])
app.include_router(sources_router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(audit_events_router, tags=["Audit History"])


@app.get("/")
def root():
    return {
        "message": "MedTrek AI backend is running",
        "status": "ok",
        "modules": [
            "RecallRadar",
            "DrugSignal",
            "Sources",
            "Audit History",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
