"""Bounded, in-memory pharmaceutical evidence PDFs, without personal-data storage."""
import logging
from collections import deque
from threading import BoundedSemaphore, Lock
from time import monotonic

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable
from app.schemas.reports import PharmaceuticalReportRequest
from app.services.pharma.evidence import drug_evidence
from app.services.report_pdf import build_pharmaceutical_pdf

logger = logging.getLogger("dav_ai.report")

router = APIRouter(prefix="/api/v1/reports", tags=["PDF evidence reports"])
_slots = BoundedSemaphore(2)
_lock = Lock()
_attempts: dict[str, deque] = {}
MAX_CLIENTS = 4096
REPORTS_PER_MINUTE = 5


def admit_report(client: str):
    now = monotonic()
    with _lock:
        for key in list(_attempts):
            if not _attempts[key] or _attempts[key][-1] <= now - 60:
                del _attempts[key]
        if client not in _attempts and len(_attempts) >= MAX_CLIENTS:
            raise HTTPException(429, "Report service is busy", headers={"Retry-After": "60"})
        attempts = _attempts.setdefault(client, deque())
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= REPORTS_PER_MINUTE:
            raise HTTPException(429, "Report limit reached. Try again in one minute.", headers={"Retry-After": "60"})
        attempts.append(now)


@router.post("/pharmaceutical", response_class=Response,
             responses={200: {"content": {"application/pdf": {}}}})
def create_pharmaceutical_report(payload: PharmaceuticalReportRequest, request: Request):
    admit_report(request.client.host if request.client else "unknown")
    if not _slots.acquire(blocking=False):
        raise HTTPException(429, "Report generation is busy", headers={"Retry-After": "5"})
    try:
        try:
            evidence = drug_evidence(payload.product_id)
        except PharmaceuticalReleaseUnavailable as exc:
            raise HTTPException(503, "Pharmaceutical release is unavailable") from exc
        if evidence is None:
            raise HTTPException(404, "Drug not found")
        try:
            content = build_pharmaceutical_pdf(payload, evidence)
        except ValueError as exc:
            raise HTTPException(413, "Evidence exceeds the bounded PDF report size") from exc
        return Response(content, media_type="application/pdf", headers={
            "Content-Disposition": 'attachment; filename="dav-ai-evidence-report.pdf"',
            "Cache-Control": "no-store, private, max-age=0",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        })
    except HTTPException:
        raise
    except Exception:
        # Never log exception text/locals: renderer failures may contain a report name.
        logger.warning("pharmaceutical_report_generation_failed")
        raise HTTPException(500, "Report generation failed") from None
    finally:
        _slots.release()
