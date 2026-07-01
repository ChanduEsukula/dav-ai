import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routes import saved_monitors
from app.routes.assistant import router as assistant_router
from app.routes.audit_events import router as audit_events_router
from app.routes.auth import router as auth_router
from app.routes.cosmetic_events import router as cosmetic_events_router
from app.routes.docs import router as docs_router
from app.routes.drug_events import router as drug_events_router
from app.routes.everyday_safety import router as everyday_safety_router
from app.routes.profile import router as profile_router
from app.routes.real_world_safety import router as real_world_safety_router
from app.routes.recalls import router as recalls_router
from app.routes.regional_health import router as regional_health_router
from app.routes.reports import router as reports_router
from app.routes.semantic_similarity import router as semantic_similarity_router
from app.routes.sources import router as sources_router
from app.routes.system import router as system_router


logger = logging.getLogger("dav_ai.request")


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
    title="Dav AI API",
    description=(
        "Healthcare safety intelligence API for recalls, adverse-event signals, "
        "source transparency, audit-aware safety briefings, and public-data PDF reports."
    ),
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
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def request_id_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    status_code = 500
    client_host = request.client.host if request.client else None

    logger.info(
        "request_started",
        extra={
            "event": "request_started",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_host": client_host,
        },
    )

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logger.exception(
            "request_failed",
            extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": client_host,
            },
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_host": client_host,
            },
        )

        if "response" in locals():
            response.headers["X-Request-ID"] = request_id


app.include_router(recalls_router, prefix="/api/v1/recalls", tags=["RecallRadar"])
app.include_router(drug_events_router, prefix="/api/v1/drug-events", tags=["DrugSignal"])
app.include_router(cosmetic_events_router, prefix="/api/v1/cosmetic-events", tags=["CosmeticSignal"])
app.include_router(everyday_safety_router, prefix="/api/v1/everyday-safety", tags=["Everyday Safety"])
app.include_router(real_world_safety_router, prefix="/api/v1/real-world-safety", tags=["Real-World Safety"])
app.include_router(sources_router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(docs_router, prefix="/api/v1/docs", tags=["Documentation"])
app.include_router(audit_events_router, tags=["Audit History"])
app.include_router(system_router, tags=["System"])
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(saved_monitors.router)
app.include_router(reports_router)
app.include_router(regional_health_router, prefix="/api/v1/regional-health", tags=["Regional Health Pulse"])
app.include_router(
    semantic_similarity_router,
    prefix="/api/v1/semantic-similarity",
    tags=["Semantic Similarity"],
)
app.include_router(assistant_router)


@app.get("/")
def root():
    return {
        "message": "Dav AI backend is running",
        "status": "ok",
        "modules": [
            "RecallRadar",
            "DrugSignal",
            "FoodRadar",
            "CosmeticSignal",
            "Everyday Safety",
            "Real-World Safety",
            "Sources",
            "Audit History",
            "Auth",
            "Profile",
            "Saved Monitors",
            "Reports",
            "Regional Health Pulse",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
