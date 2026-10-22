"""Pharmaceutical PDF renderer adapted from the existing in-memory ReportLab generator."""
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle

from app.services.pharma.evidence import official_source

CLINICAL_BLUE = colors.HexColor("#0B4F71")
MARGIN = 36
PAGE_WIDTH, PAGE_HEIGHT = LETTER
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

MAX_PDF_BYTES = 5_000_000


class LimitedPDFBuffer(BytesIO):
    def write(self, data):
        if self.tell() + len(data) > MAX_PDF_BYTES:
            raise ValueError("PDF exceeds output limit")
        return super().write(data)


def _safe_text(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)


def report_title(drug):
    name = ", ".join(drug["brand_names"]) or drug["generic_name"] or "Selected medication"
    return f"Dav AI - {name} Evidence Report"


_MISSING = object()


def build_pharmaceutical_pdf(request, evidence):
    # Bound work and memory before constructing flowables; never silently omit linked recalls.
    import json
    if len(json.dumps(evidence, ensure_ascii=False).encode("utf-8")) > 1_500_000:
        raise ValueError("Evidence too large")
    if len(evidence["recalls"]["records"]) > 200 or len(evidence["adverse_events"]["records"]) > 20:
        raise ValueError("Too many records")
    output = LimitedPDFBuffer()
    styles = getSampleStyleSheet()
    story = []

    def line(label, value=_MISSING, style="BodyText"):
        text = label if value is _MISSING else f"{label}: {_safe_text(value)}"
        story.append(Paragraph(escape(str(text)), styles[style]))
        story.append(Spacer(1, 5))

    def table(headers, rows):
        data = [[Paragraph(escape(str(v)), styles["BodyText"]) for v in row] for row in [headers, *rows]]
        t = LongTable(data, repeatRows=1, colWidths=[CONTENT_WIDTH / len(headers)] * len(headers), hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),colors.HexColor("#E0F2FE")),
                               ("VALIGN", (0,0),(-1,-1),"TOP"),
                               ("LINEBELOW", (0,0),(-1,0),0.5,CLINICAL_BLUE)]))
        story.extend([t, Spacer(1, 10)])

    drug = evidence["drug"]
    line(report_title(drug), style="Title")
    line("Prepared for", request.name)
    if request.age is not None:
        line("Age (identification only)", request.age)
    line("Generated (UTC)", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    line("Name and age identify this report only and are not used to estimate risk.")
    line("Selected medication", style="Heading1")
    for label, value in [
        ("Brand", ", ".join(drug["brand_names"])), ("Generic", drug["generic_name"]),
        ("Active ingredients", ", ".join(drug["active_ingredients"])),
        ("Strength", drug["strength"]), ("Dosage form", drug["dosage_form"]),
        ("Routes", ", ".join(drug["routes"])),
        ("NDC-listed labeler (manufacturer not independently verified)", ", ".join(drug["manufacturers"])),
        ("Product NDC", ", ".join(drug["product_ndcs"])),
        ("Package NDC", ", ".join(drug["package_ndcs"])),
        ("Product ID", drug["id"]), ("Formulation ID", drug["formulation_id"]),
        ("Application number", drug["application_number"]),
    ]:
        line(label, value)
    if drug["identity_partial"]:
        line("Identity limitations", "Product identity is partial; verify the package and formulation.")

    def coverage(section):
        c = section["coverage"]
        for key in ("state", "scope", "reason_code", "source_date", "as_of_date", "empty_message"):
            line(key.replace("_", " ").capitalize(), c.get(key))
        for limitation in c.get("limitations", []):
            line(limitation)

    line("Recall history - product-linked evidence", style="Heading1")
    recalls = evidence["recalls"]
    line("Linked records in this release", len(recalls["records"]))
    coverage(recalls)
    for record in recalls["records"]:
        line(record["recall_number"], style="Heading2")
        for key in ("product_description", "reason_for_recall", "recalling_firm", "classification",
                    "reported_status", "recall_initiation_date", "report_date", "lot_information",
                    "lot_scope", "distribution_pattern", "applicability_class", "match_method", "matched_value",
                    "source", "source_record_id"):
            line(key.replace("_", " ").capitalize(), record.get(key))
        line("Official reference URL", official_source(record.get("source_url")))

    line("Reported adverse events - ingredient-level associations", style="Heading1")
    ae = evidence["adverse_events"]
    coverage(ae)
    line(ae["summary"]["limitation"])
    for ingredient in ae["records"]:
        line(ingredient["ingredient_name"], style="Heading2")
        line("Ingredient identifier", ingredient["ingredient_id"])
        line("Ingredient coverage", ingredient["coverage"]["state"])
        for limitation in ingredient["coverage"].get("limitations", []):
            line(limitation)
        a = ingredient["analytics"]
        if not a:
            line("No stored ingredient analytics available; missing evidence is not a zero count.")
            continue
        for key in ("report_count", "serious_report_count", "serious_known_report_count", "window_start", "window_end", "count_unit", "date_basis"):
            line(key.replace("_", " ").capitalize(), a[key])
        for limitation in a.get("limitations", []):
            line(limitation)
        reactions = ingredient["top_reported_reactions"]
        monthly = ingredient.get("monthly", [])
        if len(reactions) > 50 or len(monthly) > 78:
            raise ValueError("Unbounded analytics")
        line("Top reported reactions (co-report activity; not unique patient counts)", style="Heading3")
        if reactions:
            table(["Reaction", "Co-report activity"], [(r["reaction"], r["co_report_activity"]) for r in reactions])
        line("Monthly reporting trends (deduplicated ingredient-report associations)", style="Heading3")
        if monthly:
            table(["Month", "Reports", "Marked serious"], [(m["period"], m["report_count"], m["serious_report_count"]) for m in monthly])
        else:
            line("Monthly trend data unavailable.")

    line("Sources, release and limitations", style="Heading1")
    release = evidence["release"]
    for key in ("release_id", "build_time_utc", "ndc_observation_date", "label_export_date", "window_start", "window_end"):
        line(key.replace("_", " ").capitalize(), release[key])
    line("Identity reference URL", official_source(drug["provenance"].get("source_url")))
    for source in release["sources"]:
        line("Source", source["source_name"])
        line("Source vintage", source.get("export_date") or source.get("observed_at"))
        line("Reference URL", official_source(source.get("source_url")))
    for limitation in evidence["limitations"]:
        line(limitation)
    line("Not medical advice. Verify official FDA sources and consult a qualified clinician for medical decisions.")

    def footer(c, doc):
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN, 22, f"Dav AI | FDA evidence | Page {doc.page}")
    SimpleDocTemplate(output, pagesize=LETTER, leftMargin=MARGIN, rightMargin=MARGIN,
                      topMargin=MARGIN, bottomMargin=MARGIN, title="Dav AI evidence report",
                      author="Dav AI").build(story, onFirstPage=footer, onLaterPages=footer)
    result = output.getvalue()
    if len(result) > MAX_PDF_BYTES:
        raise ValueError("PDF too large")
    return result
