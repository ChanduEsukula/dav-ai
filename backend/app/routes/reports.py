from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.schemas.reports import SafetyIntelligenceReportRequest
from app.services.report_pdf import (
    build_report_filename,
    build_safety_intelligence_pdf,
)
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search
from app.services.search_workflows.recall_search import execute_recall_search

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/safety-intelligence")
async def create_safety_intelligence_report(
    payload: SafetyIntelligenceReportRequest,
    request: Request,
) -> Response:
    """Generate a public-data safety intelligence PDF report.

    This endpoint does not persist reports or user-entered report details.
    """

    request_id = getattr(request.state, "request_id", None)

    recall_result = None
    drug_signal_result = None

    if payload.module in {"recallradar", "both"}:
        recall_result = await execute_recall_search(
            query=payload.query,
            limit=5,
            request_id=request_id,
        )

    if payload.module in {"drugsignal", "both"}:
        drug_signal_result = await execute_drug_signal_search(
            query=payload.query,
            limit=5,
            request_id=request_id,
        )

    pdf_bytes = build_safety_intelligence_pdf(
        request=payload,
        recall_result=recall_result,
        drug_signal_result=drug_signal_result,
    )

    filename = build_report_filename(payload.query)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )