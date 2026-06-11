from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from app.schemas.reports import SafetyIntelligenceReportRequest


DISCLAIMER = (
    "Generated from public FDA/openFDA data. Not medical advice, diagnosis, "
    "treatment guidance, or a medication-change recommendation. FAERS reports "
    "do not prove causation. Verify official sources and consult qualified professionals."
)

FOODRADAR_DISCLAIMER = (
    "Generated from public FDA/openFDA and USDA FSIS recall data. Not medical advice "
    "or official recall instructions. Food and supplement recall records do not prove "
    "safety or risk by themselves. Verify exact product, package, lot code, firm, and "
    "official source notices."
)

COSMETICSIGNAL_DISCLAIMER = (
    "Generated from public FDA/openFDA cosmetic adverse-event report data. "
    "Cosmetic public reporting records do not prove product danger, medical risk, "
    "causation, incidence, or source completeness. Verify exact product details "
    "and official source records."
)

PRIVACY_NOTE = (
    "Do not include personal medical history, diagnoses, prescription history, "
    "patient records, insurance information, addresses, or private health information."
)

ROLE_LABELS = {
    "consumer": "Consumer",
    "pharmacy": "Pharmacy",
    "clinic": "Clinic",
    "public_health_analyst": "Public Health / Analyst",
    "student_researcher": "Student / Researcher",
}

MODULE_LABELS = {
    "recallradar": "RecallRadar",
    "drugsignal": "DrugSignal",
    "foodradar": "FoodRadar",
    "cosmeticsignal": "CosmeticSignal",
    "both": "RecallRadar + DrugSignal",
}

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 36
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN * 2)

INK = colors.HexColor("#102033")
DEEP_INK = colors.HexColor("#061523")
MUTED = colors.HexColor("#607083")
SOFT_MUTED = colors.HexColor("#7F8FA3")
CLINICAL_BLUE = colors.HexColor("#0B4F71")
DEEP_TEAL = colors.HexColor("#007B87")
TEAL = colors.HexColor("#008B8B")
AQUA = colors.HexColor("#19B6C9")
MEDICAL_GREEN = colors.HexColor("#24B47E")
PAGE_BG = colors.HexColor("#F4FBFB")
ICE = colors.HexColor("#EEF8FA")
CARD_BORDER = colors.HexColor("#DDECEF")
SOFT_PANEL = colors.HexColor("#F8FBFC")
PILL_BG = colors.HexColor("#E0F2FE")
PILL_TEXT = colors.HexColor("#075985")
SUCCESS_BG = colors.HexColor("#DCFCE7")
SUCCESS_TEXT = colors.HexColor("#166534")
WARNING_BG = colors.HexColor("#FEF2F2")
WARNING_BORDER = colors.HexColor("#FECACA")
WARNING_TEXT = colors.HexColor("#7F1D1D")


def _safe_text(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)


def _safe_filename_part(value: str) -> str:
    allowed: list[str] = []

    for character in value.lower().strip():
        if character.isalnum():
            allowed.append(character)
        elif character in {" ", "-", "_"}:
            allowed.append("-")

    cleaned = "".join(allowed).strip("-")
    return cleaned or "report"


def build_report_filename(query: str) -> str:
    return f"dav-ai-public-data-report-{_safe_filename_part(query)}.pdf"


def _style(
    *,
    font_name: str = "Helvetica",
    font_size: float = 8.5,
    leading: float = 11,
    color=INK,
) -> ParagraphStyle:
    return ParagraphStyle(
        "dav_ai_report_style",
        fontName=font_name,
        fontSize=font_size,
        leading=leading,
        textColor=color,
    )


def _draw_paragraph(
    c: canvas.Canvas,
    text: str,
    *,
    x: float,
    y_top: float,
    width: float,
    font_name: str = "Helvetica",
    font_size: float = 8.5,
    leading: float = 11.5,
    color=INK,
) -> float:
    paragraph = Paragraph(
        escape(_safe_text(text)),
        _style(
            font_name=font_name,
            font_size=font_size,
            leading=leading,
            color=color,
        ),
    )
    _, height = paragraph.wrap(width, 1000)
    paragraph.drawOn(c, x, y_top - height)
    return height


def _draw_background(c: canvas.Canvas) -> None:
    c.setFillColor(PAGE_BG)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)

    c.setStrokeColor(colors.HexColor("#E7F2F4"))
    c.setLineWidth(0.25)

    grid = 54
    x = 0
    while x <= PAGE_WIDTH:
        c.line(x, 0, x, PAGE_HEIGHT)
        x += grid

    y = 0
    while y <= PAGE_HEIGHT:
        c.line(0, y, PAGE_WIDTH, y)
        y += grid

    c.setFillColor(colors.Color(0.10, 0.71, 0.79, alpha=0.07))
    c.circle(62, PAGE_HEIGHT - 42, 118, stroke=0, fill=1)

    c.setFillColor(colors.Color(0.14, 0.71, 0.49, alpha=0.055))
    c.circle(PAGE_WIDTH - 42, PAGE_HEIGHT - 52, 126, stroke=0, fill=1)


def _draw_card(
    c: canvas.Canvas,
    *,
    x: float,
    y_top: float,
    width: float,
    height: float,
    radius: float = 18,
    fill_color=colors.white,
    border_color=CARD_BORDER,
    shadow: bool = True,
) -> None:
    if shadow:
        c.setFillColor(colors.Color(0.06, 0.12, 0.20, alpha=0.035))
        c.roundRect(x + 1.5, y_top - height - 2, width, height, radius, stroke=0, fill=1)

    c.setFillColor(fill_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(0.55)
    c.roundRect(x, y_top - height, width, height, radius, stroke=1, fill=1)


def _draw_brand_mark(c: canvas.Canvas, x: float, y_top: float, size: float = 28) -> None:
    c.setFillColor(CLINICAL_BLUE)
    c.roundRect(x, y_top - size, size, size, 9, stroke=0, fill=1)

    c.setFillColor(DEEP_TEAL)
    c.roundRect(x + 4, y_top - size + 4, size - 8, size - 8, 7, stroke=0, fill=1)

    c.setFillColor(MEDICAL_GREEN)
    c.circle(x + size - 8, y_top - 8, 5.5, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x + size / 2, y_top - size + 8, "+")


def _draw_header(
    c: canvas.Canvas,
    *,
    generated_at: str,
    module_label: str,
    query: str,
) -> float:
    y_top = PAGE_HEIGHT - 28
    height = 54

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=27,
        fill_color=colors.Color(1, 1, 1, alpha=0.92),
        border_color=colors.white,
    )

    _draw_brand_mark(c, MARGIN + 16, y_top - 13, size=28)

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN + 56, y_top - 24, "Dav AI")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN + 56, y_top - 37, "Public-data safety intelligence")

    pill_x = PAGE_WIDTH - MARGIN - 148
    _draw_pill(
        c,
        x=pill_x,
        y_top=y_top - 16,
        text=module_label,
        fill_color=PILL_BG,
        text_color=PILL_TEXT,
    )

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.2)
    c.drawRightString(
        PAGE_WIDTH - MARGIN - 18,
        y_top - 39,
        f"{query} · {generated_at[:10]}",
    )

    return y_top - height - 18


def _draw_footer(c: canvas.Canvas, page_number: int) -> None:
    c.setStrokeColor(colors.HexColor("#DDECEF"))
    c.setLineWidth(0.5)
    c.line(MARGIN, 29, PAGE_WIDTH - MARGIN, 29)

    c.setFillColor(SOFT_MUTED)
    c.setFont("Helvetica", 6.8)
    c.drawString(
        MARGIN,
        17,
        "Dav AI · Public FDA/openFDA data review · Not medical advice",
    )
    c.drawRightString(PAGE_WIDTH - MARGIN, 17, f"Page {page_number}")


def _draw_pill(
    c: canvas.Canvas,
    *,
    x: float,
    y_top: float,
    text: str,
    fill_color=PILL_BG,
    text_color=PILL_TEXT,
) -> float:
    label = text.upper()
    c.setFont("Helvetica-Bold", 6.8)
    text_width = c.stringWidth(label, "Helvetica-Bold", 6.8)
    width = text_width + 16
    height = 16

    c.setFillColor(fill_color)
    c.roundRect(x, y_top - height, width, height, 8, stroke=0, fill=1)

    c.setFillColor(text_color)
    c.drawString(x + 8, y_top - 11.2, label)

    return width


def _draw_title_area(
    c: canvas.Canvas,
    *,
    y_top: float,
    title: str,
    subtitle: str,
) -> float:
    c.setFillColor(DEEP_TEAL)
    c.setFont("Helvetica-Bold", 7.2)
    c.drawString(MARGIN, y_top, "PUBLIC DATA INTELLIGENCE REPORT")

    y_top -= 27

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MARGIN, y_top, title)

    y_top -= 12
    used = _draw_paragraph(
        c,
        subtitle,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH - 30,
        font_size=8.6,
        leading=11.5,
        color=MUTED,
    )

    return y_top - used - 10


def _draw_report_details_strip(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    y_top: float,
    generated_at: str,
) -> float:
    height = 66

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=18,
        fill_color=colors.Color(1, 1, 1, alpha=0.94),
        border_color=colors.white,
    )

    items = [
        ("Prepared for", request.prepared_for),
        ("Role", ROLE_LABELS.get(request.role, request.role)),
        ("Organization", request.organization or "N/A"),
        ("Generated", generated_at[:19].replace("T", " ") + " UTC"),
    ]

    col_width = CONTENT_WIDTH / 4
    x = MARGIN

    for label, value in items:
        c.setFillColor(SOFT_MUTED)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x + 12, y_top - 20, label.upper())

        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 8.6)
        c.drawString(x + 12, y_top - 39, _safe_text(value)[:28])

        x += col_width

    return y_top - height - 14


def _draw_score_card(
    c: canvas.Canvas,
    *,
    x: float,
    y_top: float,
    width: float,
    height: float,
    score: Any,
    label: Any,
    priority: Any,
    confidence: Any,
) -> None:
    _draw_card(
        c,
        x=x,
        y_top=y_top,
        width=width,
        height=height,
        radius=22,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_TEAL)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 18, y_top - 22, "REVIEW PRIORITY")

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 42)
    c.drawString(x + 18, y_top - 70, _safe_text(score))

    c.setFillColor(CLINICAL_BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 95, y_top - 68, _safe_text(label))

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(x + 20, y_top - 94, f"Review status: {_safe_text(priority)}")
    c.drawString(x + 20, y_top - 110, f"Evidence confidence: {_safe_text(confidence)}")

    _draw_pill(
        c,
        x=x + 18,
        y_top=y_top - 122,
        text="Public data only",
        fill_color=WARNING_BG,
        text_color=WARNING_TEXT,
    )


def _draw_mini_metric(
    c: canvas.Canvas,
    *,
    x: float,
    y_top: float,
    width: float,
    height: float,
    label: str,
    value: Any,
    note: str,
) -> None:
    _draw_card(
        c,
        x=x,
        y_top=y_top,
        width=width,
        height=height,
        radius=17,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_TEAL)
    c.setFont("Helvetica-Bold", 6.6)
    c.drawString(x + 14, y_top - 18, label.upper())

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(x + 14, y_top - 39, _safe_text(value)[:23])

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.2)
    c.drawString(x + 14, y_top - 54, note[:30])


def _draw_source_strip(
    c: canvas.Canvas,
    *,
    y_top: float,
    source_name: Any,
    endpoint: Any,
    audit_id: Any,
) -> float:
    height = 58

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=18,
        fill_color=ICE,
        border_color=colors.HexColor("#BAE6FD"),
        shadow=False,
    )

    columns = [
        ("Source", source_name),
        ("Endpoint", endpoint),
        ("Audit ID", audit_id),
    ]

    col_widths = [140, 245, CONTENT_WIDTH - 385]
    x = MARGIN + 14

    for index, (label, value) in enumerate(columns):
        c.setFillColor(DEEP_TEAL)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x, y_top - 18, label.upper())

        c.setFillColor(INK)
        c.setFont("Helvetica", 7.2)
        c.drawString(x, y_top - 36, _safe_text(value)[:44])

        x += col_widths[index]

    return y_top - height - 12


def _draw_reactions_card(
    c: canvas.Canvas,
    *,
    y_top: float,
    reactions: list[dict[str, Any]],
) -> float:
    height = 204

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=22,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN + 18, y_top - 24, "Top Reported Reactions")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(
        MARGIN + 18,
        y_top - 39,
        "Counts reflect returned public records, not incidence or causation.",
    )

    if not reactions:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN + 18, y_top - 72, "No top reactions were returned for this query.")
        return y_top - height - 12

    max_count = max(int(reaction.get("count", 0) or 0) for reaction in reactions[:8]) or 1
    row_y = y_top - 66

    for reaction in reactions[:8]:
        name = _safe_text(reaction.get("reaction", "Unknown"))[:48]
        count = int(reaction.get("count", 0) or 0)
        bar_width = 210 * (count / max_count)

        c.setFillColor(SOFT_PANEL)
        c.roundRect(MARGIN + 18, row_y - 14, CONTENT_WIDTH - 36, 18, 9, stroke=0, fill=1)

        c.setFillColor(DEEP_TEAL)
        c.roundRect(MARGIN + 218, row_y - 10, bar_width, 8, 4, stroke=0, fill=1)

        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 7.8)
        c.drawString(MARGIN + 30, row_y - 7, name)

        c.setFillColor(DEEP_TEAL)
        c.setFont("Helvetica-Bold", 7.8)
        c.drawRightString(PAGE_WIDTH - MARGIN - 30, row_y - 7, f"{count}")

        row_y -= 20

    return y_top - height - 12


def _draw_safety_card(
    c: canvas.Canvas,
    *,
    y_top: float,
    disclaimer: str = DISCLAIMER,
) -> float:
    height = 68

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=18,
        fill_color=WARNING_BG,
        border_color=WARNING_BORDER,
        shadow=False,
    )

    c.setFillColor(WARNING_TEXT)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(MARGIN + 16, y_top - 18, "SAFETY BOUNDARY")

    _draw_paragraph(
        c,
        disclaimer,
        x=MARGIN + 16,
        y_top=y_top - 26,
        width=CONTENT_WIDTH - 32,
        font_name="Helvetica-Bold",
        font_size=7.6,
        leading=10.2,
        color=WARNING_TEXT,
    )

    return y_top - height - 10


def _draw_privacy_footer_note(c: canvas.Canvas, *, y_top: float) -> float:
    c.setFillColor(SOFT_MUTED)
    c.setFont("Helvetica", 6.8)
    c.drawString(MARGIN, y_top, PRIVACY_NOTE[:145])
    return y_top - 10


def _draw_drug_signal_one_page(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    drug_result: dict[str, Any] | None,
    generated_at: str,
) -> None:
    _draw_background(c)
    y = _draw_header(
        c,
        generated_at=generated_at,
        module_label="DrugSignal",
        query=request.query,
    )

    y = _draw_title_area(
        c,
        y_top=y,
        title="DrugSignal Public Data Intelligence",
        subtitle=(
            "A compact public-data reporting-pattern summary for review, "
            "audit traceability, and safety awareness."
        ),
    )

    y = _draw_report_details_strip(
        c,
        request=request,
        y_top=y,
        generated_at=generated_at,
    )

    score = (drug_result or {}).get("intelligence_score") or {}
    trend = (drug_result or {}).get("trend_snapshot") or {}
    reactions = (drug_result or {}).get("top_reactions") or []

    score_card_width = 250
    metric_x = MARGIN + score_card_width + 12
    metric_width = CONTENT_WIDTH - score_card_width - 12

    _draw_score_card(
        c,
        x=MARGIN,
        y_top=y,
        width=score_card_width,
        height=150,
        score=score.get("score", "N/A"),
        label=score.get("label", "N/A"),
        priority=score.get("review_priority", "N/A"),
        confidence=score.get("data_confidence", "N/A"),
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y,
        width=metric_width,
        height=68,
        label="Records returned",
        value=(drug_result or {}).get("count", 0),
        note="Public FAERS-style records",
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y - 82,
        width=metric_width,
        height=68,
        label="Trend snapshot",
        value=trend.get("label", "N/A"),
        note="Compared with stored audit history",
    )

    y -= 166

    y = _draw_reactions_card(
        c,
        y_top=y,
        reactions=reactions,
    )

    y = _draw_source_strip(
        c,
        y_top=y,
        source_name=(drug_result or {}).get("source_name"),
        endpoint=(drug_result or {}).get("endpoint"),
        audit_id=((drug_result or {}).get("audit") or {}).get("audit_id"),
    )

    y = _draw_safety_card(c, y_top=y)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 1)


def _draw_recall_one_page(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    recall_result: dict[str, Any] | None,
    generated_at: str,
) -> None:
    _draw_background(c)
    y = _draw_header(
        c,
        generated_at=generated_at,
        module_label="RecallRadar",
        query=request.query,
    )

    y = _draw_title_area(
        c,
        y_top=y,
        title="RecallRadar Public Data Intelligence",
        subtitle=(
            "A compact public-data recall summary for review, traceability, "
            "and official-source verification."
        ),
    )

    y = _draw_report_details_strip(
        c,
        request=request,
        y_top=y,
        generated_at=generated_at,
    )

    results = (recall_result or {}).get("results") or []
    first = results[0] if results else {}
    review_priority = first.get("risk_score") or {}

    score_card_width = 250
    metric_x = MARGIN + score_card_width + 12
    metric_width = CONTENT_WIDTH - score_card_width - 12

    _draw_score_card(
        c,
        x=MARGIN,
        y_top=y,
        width=score_card_width,
        height=150,
        score=review_priority.get("score", "N/A"),
        label=review_priority.get("label", first.get("classification", "N/A")),
        priority=first.get("status", "N/A"),
        confidence=first.get("classification", "N/A"),
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y,
        width=metric_width,
        height=68,
        label="Records returned",
        value=(recall_result or {}).get("count", 0),
        note="Public recall records",
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y - 82,
        width=metric_width,
        height=68,
        label="Recall status",
        value=first.get("status", "N/A"),
        note="First returned record",
    )

    y -= 166

    y = _draw_source_strip(
        c,
        y_top=y,
        source_name=(recall_result or {}).get("source_name"),
        endpoint=(recall_result or {}).get("endpoint"),
        audit_id=((recall_result or {}).get("audit") or {}).get("audit_id"),
    )

    record_rows = [
        ("Product", first.get("product_description")),
        ("Classification", first.get("classification")),
        ("Status", first.get("status")),
        ("Recalling firm", first.get("recalling_firm")),
        ("Initiation date", first.get("recall_initiation_date")),
        ("Reason", first.get("reason_for_recall")),
    ]

    y = _draw_compact_detail_card(
        c,
        y_top=y,
        title="First Returned Recall Record",
        rows=record_rows,
    )

    y = _draw_safety_card(c, y_top=y)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 1)


def _draw_foodradar_one_page(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    everyday_safety_result: dict[str, Any] | None,
    generated_at: str,
) -> None:
    _draw_background(c)
    y = _draw_header(
        c,
        generated_at=generated_at,
        module_label="FoodRadar",
        query=request.query,
    )

    y = _draw_title_area(
        c,
        y_top=y,
        title="FoodRadar Public Data Intelligence",
        subtitle=(
            "A compact public-data food and supplement recall summary for review, "
            "traceability, and official-source verification."
        ),
    )

    y = _draw_report_details_strip(
        c,
        request=request,
        y_top=y,
        generated_at=generated_at,
    )

    results = (everyday_safety_result or {}).get("results") or []
    first = results[0] if results else {}
    review_priority = first.get("risk_score") or {}

    score_card_width = 250
    metric_x = MARGIN + score_card_width + 12
    metric_width = CONTENT_WIDTH - score_card_width - 12

    _draw_score_card(
        c,
        x=MARGIN,
        y_top=y,
        width=score_card_width,
        height=150,
        score=review_priority.get("score", "N/A"),
        label=review_priority.get("label", first.get("classification", "N/A")),
        priority=first.get("status", "N/A"),
        confidence=first.get("classification", "N/A"),
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y,
        width=metric_width,
        height=68,
        label="Records returned",
        value=(everyday_safety_result or {}).get("count", 0),
        note="Public food recall records",
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y - 82,
        width=metric_width,
        height=68,
        label="Search strategy",
        value=(everyday_safety_result or {}).get("search_strategy_used", "N/A"),
        note="FoodRadar query handling",
    )

    y -= 166

    y = _draw_source_strip(
        c,
        y_top=y,
        source_name=(everyday_safety_result or {}).get("source_name"),
        endpoint=(everyday_safety_result or {}).get("endpoint"),
        audit_id=((everyday_safety_result or {}).get("audit") or {}).get("audit_id"),
    )

    record_rows = [
        ("Product", first.get("product_description")),
        ("Classification", first.get("classification")),
        ("Status", first.get("status")),
        ("Recalling firm", first.get("recalling_firm")),
        ("Initiation date", first.get("recall_initiation_date")),
        ("Reason", first.get("reason_for_recall")),
    ]

    y = _draw_compact_detail_card(
        c,
        y_top=y,
        title="First Returned Food / Supplement Recall Record",
        rows=record_rows,
    )

    y = _draw_safety_card(c, y_top=y, disclaimer=FOODRADAR_DISCLAIMER)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 1)

    c.showPage()
    _draw_background(c)
    _draw_header(
        c,
        generated_at=generated_at,
        module_label="FoodRadar Details",
        query=request.query,
    )

    y = PAGE_HEIGHT - 108
    limitations = (everyday_safety_result or {}).get("limitations") or []
    limitation_text = " ".join(str(item) for item in limitations[:2]) or (
        "No matching public records found does not mean the product is safe. "
        "Verify the exact product, package, lot code, and official source notice."
    )

    y = _draw_compact_detail_card(
        c,
        y_top=y,
        title="Public Data Limitations",
        rows=[
            ("Boundary", "No matching public records found does not mean the product is safe."),
            ("Verify", "Check exact product, package, lot code, firm, and official notice."),
            ("Sources", (everyday_safety_result or {}).get("source_name")),
            ("Timestamp", (everyday_safety_result or {}).get("retrieval_timestamp")),
            ("Disclaimer", (everyday_safety_result or {}).get("public_data_disclaimer")),
            ("Limitations", limitation_text),
        ],
    )

    sources_checked = (everyday_safety_result or {}).get("sources_checked") or []
    source_rows = [
        (
            _safe_text(source.get("source_name") or source.get("source_id")),
            f"{_safe_text(source.get('upstream_status'))} · records: {_safe_text(source.get('record_count'))}",
        )
        for source in sources_checked[:6]
        if isinstance(source, dict)
    ]

    if source_rows:
        y = _draw_compact_detail_card(
            c,
            y_top=y,
            title="Sources Checked",
            rows=source_rows,
        )

    y = _draw_safety_card(c, y_top=y, disclaimer=FOODRADAR_DISCLAIMER)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 2)


def _draw_cosmetic_signal_one_page(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    cosmetic_signal_result: dict[str, Any] | None,
    generated_at: str,
) -> None:
    _draw_background(c)
    y = _draw_header(
        c,
        generated_at=generated_at,
        module_label="CosmeticSignal",
        query=request.query,
    )

    y = _draw_title_area(
        c,
        y_top=y,
        title="CosmeticSignal Public Data Intelligence",
        subtitle=(
            "A compact public-data cosmetic adverse-event reporting-pattern summary "
            "for review, audit traceability, and source-aware safety awareness."
        ),
    )

    y = _draw_report_details_strip(
        c,
        request=request,
        y_top=y,
        generated_at=generated_at,
    )

    score = (cosmetic_signal_result or {}).get("signal_score") or {}
    results = (cosmetic_signal_result or {}).get("results") or []
    first = results[0] if results else {}

    score_card_width = 250
    metric_x = MARGIN + score_card_width + 12
    metric_width = CONTENT_WIDTH - score_card_width - 12

    _draw_score_card(
        c,
        x=MARGIN,
        y_top=y,
        width=score_card_width,
        height=150,
        score=score.get("score", "N/A"),
        label=score.get("label", "N/A"),
        priority=score.get("review_priority", "N/A"),
        confidence=score.get("data_confidence", "N/A"),
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y,
        width=metric_width,
        height=68,
        label="Records returned",
        value=(cosmetic_signal_result or {}).get("count", 0),
        note="Public cosmetic reports",
    )

    _draw_mini_metric(
        c,
        x=metric_x,
        y_top=y - 82,
        width=metric_width,
        height=68,
        label="Public signal",
        value=score.get("label", "N/A"),
        note="Reporting pattern only",
    )

    y -= 166

    y = _draw_source_strip(
        c,
        y_top=y,
        source_name=(cosmetic_signal_result or {}).get("source_name"),
        endpoint=(cosmetic_signal_result or {}).get("endpoint"),
        audit_id=((cosmetic_signal_result or {}).get("audit") or {}).get("audit_id"),
    )

    record_rows = [
        ("Product", first.get("product_description") or first.get("product")),
        ("Brand", first.get("brand_name") or first.get("brand")),
        ("Report date", first.get("report_date")),
        ("Reported event", first.get("event") or first.get("reaction")),
        ("Outcome", first.get("outcome")),
        ("Source", first.get("source")),
    ]

    y = _draw_compact_detail_card(
        c,
        y_top=y,
        title="First Returned Cosmetic Report Record",
        rows=record_rows,
    )

    y = _draw_safety_card(c, y_top=y, disclaimer=COSMETICSIGNAL_DISCLAIMER)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 1)


def _draw_compact_detail_card(
    c: canvas.Canvas,
    *,
    y_top: float,
    title: str,
    rows: list[tuple[str, Any]],
) -> float:
    visible_rows = rows[:6]
    title_height = 38
    row_gap = 11
    min_row_height = 25
    bottom_padding = 18

    value_x = MARGIN + 142
    value_width = CONTENT_WIDTH - 166

    measured_row_heights: list[float] = []

    for _, value in visible_rows:
        paragraph = Paragraph(
            escape(_safe_text(value)),
            _style(font_size=7.4, leading=9.2, color=INK),
        )
        _, paragraph_height = paragraph.wrap(value_width, 1000)
        measured_row_heights.append(max(min_row_height, paragraph_height + 8))

    content_height = sum(measured_row_heights)
    if measured_row_heights:
        content_height += row_gap * (len(measured_row_heights) - 1)

    height = max(206, title_height + content_height + bottom_padding)

    _draw_card(
        c,
        x=MARGIN,
        y_top=y_top,
        width=CONTENT_WIDTH,
        height=height,
        radius=22,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN + 18, y_top - 24, title)

    row_y = y_top - 52

    for index, (label, value) in enumerate(visible_rows):
        c.setFillColor(SOFT_MUTED)
        c.setFont("Helvetica-Bold", 6.6)
        c.drawString(MARGIN + 18, row_y, label.upper())

        _draw_paragraph(
            c,
            _safe_text(value),
            x=value_x,
            y_top=row_y + 4,
            width=value_width,
            font_size=7.4,
            leading=9.2,
            color=INK,
        )

        row_height = measured_row_heights[index]
        c.setStrokeColor(colors.HexColor("#E8EEF2"))
        c.setLineWidth(0.4)
        c.line(
            MARGIN + 18,
            row_y - row_height + 8,
            MARGIN + CONTENT_WIDTH - 18,
            row_y - row_height + 8,
        )

        row_y -= row_height + row_gap

    return y_top - height - 16


def _draw_both_modules_report(
    c: canvas.Canvas,
    *,
    request: SafetyIntelligenceReportRequest,
    recall_result: dict[str, Any] | None,
    drug_signal_result: dict[str, Any] | None,
    generated_at: str,
) -> None:
    _draw_background(c)
    y = _draw_header(
        c,
        generated_at=generated_at,
        module_label="RecallRadar + DrugSignal",
        query=request.query,
    )

    y = _draw_title_area(
        c,
        y_top=y,
        title="Combined Public Data Intelligence",
        subtitle=(
            "A two-module public-data summary combining recall records and "
            "adverse-event reporting patterns."
        ),
    )

    y = _draw_report_details_strip(
        c,
        request=request,
        y_top=y,
        generated_at=generated_at,
    )

    recall_results = (recall_result or {}).get("results") or []
    first_recall = recall_results[0] if recall_results else {}
    recall_priority = first_recall.get("risk_score") or {}
    drug_score = (drug_signal_result or {}).get("intelligence_score") or {}

    card_gap = 12
    card_width = (CONTENT_WIDTH - card_gap) / 2

    _draw_card(
        c,
        x=MARGIN,
        y_top=y,
        width=card_width,
        height=150,
        radius=22,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_TEAL)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(MARGIN + 18, y - 22, "RECALLRADAR REVIEW PRIORITY")

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(MARGIN + 18, y - 60, _safe_text(recall_priority.get("score", "N/A")))

    c.setFillColor(CLINICAL_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN + 18, y - 86, _safe_text(recall_priority.get("label", "N/A")))

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(
        MARGIN + 18,
        y - 110,
        f"Records: {_safe_text((recall_result or {}).get('count', 0))}",
    )

    right_x = MARGIN + card_width + card_gap

    _draw_card(
        c,
        x=right_x,
        y_top=y,
        width=card_width,
        height=150,
        radius=22,
        fill_color=colors.white,
        border_color=colors.white,
    )

    c.setFillColor(DEEP_TEAL)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(right_x + 18, y - 22, "DRUGSIGNAL REVIEW PRIORITY")

    c.setFillColor(DEEP_INK)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(right_x + 18, y - 60, _safe_text(drug_score.get("score", "N/A")))

    c.setFillColor(CLINICAL_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(right_x + 18, y - 86, _safe_text(drug_score.get("label", "N/A")))

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(
        right_x + 18,
        y - 110,
        f"Records: {_safe_text((drug_signal_result or {}).get('count', 0))}",
    )

    y -= 168

    y = _draw_source_strip(
        c,
        y_top=y,
        source_name="openFDA Drug Enforcement + Drug Event",
        endpoint="api.fda.gov public endpoints",
        audit_id="See module-specific audit events",
    )

    y = _draw_safety_card(c, y_top=y)
    _draw_privacy_footer_note(c, y_top=y)

    _draw_footer(c, 1)

    c.showPage()

    _draw_background(c)
    _draw_header(
        c,
        generated_at=generated_at,
        module_label="Module Details",
        query=request.query,
    )

    y = PAGE_HEIGHT - 108

    y = _draw_compact_detail_card(
        c,
        y_top=y,
        title="RecallRadar Detail",
        rows=[
            ("Product", first_recall.get("product_description")),
            ("Classification", first_recall.get("classification")),
            ("Status", first_recall.get("status")),
            ("Reason", first_recall.get("reason_for_recall")),
            ("Firm", first_recall.get("recalling_firm")),
            ("Audit ID", ((recall_result or {}).get("audit") or {}).get("audit_id")),
        ],
    )

    reactions = (drug_signal_result or {}).get("top_reactions") or []
    y = _draw_reactions_card(c, y_top=y, reactions=reactions)

    _draw_footer(c, 2)


def build_safety_intelligence_pdf(
    *,
    request: SafetyIntelligenceReportRequest,
    recall_result: dict[str, Any] | None = None,
    drug_signal_result: dict[str, Any] | None = None,
    everyday_safety_result: dict[str, Any] | None = None,
    cosmetic_signal_result: dict[str, Any] | None = None,
) -> bytes:
    """Build a compact Dav AI-branded public-data PDF report."""

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    pdf.setTitle("Dav AI Public Data Intelligence Report")

    generated_at = datetime.now(timezone.utc).isoformat()

    if request.module == "drugsignal":
        _draw_drug_signal_one_page(
            pdf,
            request=request,
            drug_result=drug_signal_result,
            generated_at=generated_at,
        )
    elif request.module == "recallradar":
        _draw_recall_one_page(
            pdf,
            request=request,
            recall_result=recall_result,
            generated_at=generated_at,
        )
    elif request.module == "foodradar":
        _draw_foodradar_one_page(
            pdf,
            request=request,
            everyday_safety_result=everyday_safety_result,
            generated_at=generated_at,
        )
    elif request.module == "cosmeticsignal":
        _draw_cosmetic_signal_one_page(
            pdf,
            request=request,
            cosmetic_signal_result=cosmetic_signal_result,
            generated_at=generated_at,
        )
    else:
        _draw_both_modules_report(
            pdf,
            request=request,
            recall_result=recall_result,
            drug_signal_result=drug_signal_result,
            generated_at=generated_at,
        )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()