from contextlib import asynccontextmanager
import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.services.report_limits import ReportPrivacyMiddleware
from app.services.public_evidence import PublicEvidenceMiddleware

from app.db.database import is_deployed_environment
from app.db.pharma.release_connection import (
    PharmaceuticalReleaseUnavailable,
    connect_release,
)
from app.routes.drug_safety import router as drug_safety_router
from app.routes.drugs import router as drugs_router
from app.routes.reports import router as reports_router
from app.routes.evidence import router as evidence_router
from app.routes.medications import router as medications_router


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


class PharmaceuticalAPI(FastAPI):
    def build_middleware_stack(self):
        # Wrap ServerErrorMiddleware too: even unexpected 500s must be private.
        return PublicEvidenceMiddleware(ReportPrivacyMiddleware(super().build_middleware_stack()))


@asynccontextmanager
async def application_lifespan(application):
    strict = (is_deployed_environment() or "DAV_AI_PHARMA_ARTIFACT_ROOT" in os.environ
              or os.getenv("DAV_AI_PHARMA_REQUIRE_READY_AT_STARTUP") == "1")
    if strict:
        try:
            connection = connect_release()
            connection.close()
            if is_deployed_environment():
                from app.security.production_authorization import require_production_authorization
                grant = require_production_authorization()
                logging.getLogger("uvicorn.error").info(
                    "public_evidence_authorization_verified approval_sha256=%s", grant.payload_sha256
                )
        except Exception:
            logger.error("pharmaceutical_startup_refused")
            raise RuntimeError("Pharmaceutical startup refused: artifact unavailable or serving unauthorized") from None
    yield


app = PharmaceuticalAPI(
    lifespan=application_lifespan,
    title="Dav AI API",
    description=(
        "Frozen FDA pharmaceutical evidence: recalls, reported adverse events, "
        "coverage, provenance, and personalized PDF evidence reports."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def request_id_logging_middleware(request: Request, call_next):
    supplied_id = request.headers.get("X-Request-ID", "")
    # Untrusted identifiers must not introduce unbounded or control-character log data.
    request_id = supplied_id if (0 < len(supplied_id) <= 64 and all(
        c.isascii() and (c.isalnum() or c in "-_") for c in supplied_id
    )) else str(uuid.uuid4())
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
        logger.error(
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


app.include_router(drugs_router)
app.include_router(drug_safety_router)
app.include_router(reports_router)
app.include_router(evidence_router)
app.include_router(medications_router)


@app.get("/")
def root():
    return {
        "message": "Dav AI backend is running",
        "status": "ok",
        "modules": ["Drug recalls", "Reported adverse events", "PDF evidence reports"],
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/ready")
def readiness_check():
    connection = None

    try:
        connection = connect_release()
        connection.execute("SELECT 1").fetchone()

    except (PharmaceuticalReleaseUnavailable, OSError):
        raise HTTPException(
            status_code=503,
            detail="Pharmaceutical service is not ready",
        )

    except Exception:
        logger.exception("pharmaceutical_readiness_check_failed")
        raise HTTPException(
            status_code=503,
            detail="Pharmaceutical service is not ready",
        )

    finally:
        if connection is not None:
            connection.close()

    return {
        "status": "ready",
        "pharmaceutical_database": "available",
    }


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError):
    if request.url.path.rstrip("/") == "/api/v1/reports/pharmaceutical":
        # Pydantic normally reflects the invalid name/age in input/ctx fields.
        return JSONResponse(status_code=422, content={"detail": "Invalid report fields"})
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)
