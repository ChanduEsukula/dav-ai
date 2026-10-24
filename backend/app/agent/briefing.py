"""Deterministic validation/assembly of research sources, without model summaries."""
from datetime import date

from pydantic import ValidationError

from app.agent.contracts import AgentRejected
from app.agent.evidence import evidence_card
from app.agent.research_contracts import (
    BriefingSection, FaersCard, LabelCard, MedicationIdentity, RecallCard,
    ResearchBriefing, RoutingInfo, TOOLS,
)
from app.services.pharma.evidence import LIMITATIONS

LABEL_FIELDS = {"boxed_warning": "boxed_warning", "warnings_and_precautions": "warnings_and_cautions",
                "warnings": "warnings", "contraindications": "contraindications",
                "drug_interactions": "drug_interactions", "adverse_reactions": "adverse_reactions"}
FAERS_LIMITATION = (
    "Ingredient-level spontaneous FAERS reporting associations only. These are not observations attributed "
    "to the selected NDC and do not establish causation, incidence, comparative safety or individual risk. "
    "Do not sum ingredients into a product total. No denominators, risk scores or signal classifications are inferred."
)


def _date(value):
    try:
        if type(value) is not str or len(value) != 10:
            raise ValueError()
        date.fromisoformat(value)
    except (ValueError, TypeError):
        raise AgentRejected("missing_source_snapshot") from None


def validate_card(category, reference, public_product, product, result):
    if (not isinstance(result, dict) or result.get("product_id") != product["product_id"]
            or result.get("product_ndcs") != product["product_ndcs"]):
        raise AgentRejected("product_binding_changed")
    try:
        if category == "recalls":
            card = RecallCard.model_validate({**evidence_card(reference, public_product, product, result),
                                              "release": result["release"]})
        elif category == "labels":
            raw = result["evidence"]
            coverage = raw["coverage"]
            _date(coverage.get("source_date"))
            missing = []
            for record in raw["records"]:
                _date(record.get("effective_date"))
                if not record.get("source_record_id") or not record.get("label_set_id") or not record.get("label_version"):
                    raise AgentRejected("missing_source_provenance")
                for field, section_name in LABEL_FIELDS.items():
                    section = record["section_states"].get(section_name)
                    text = record.get(field)
                    if section is None or section.get("state") != "READY":
                        if text is not None:
                            raise AgentRejected("invalid_label_section_state")
                        missing.append(field)
                    elif not text or text != section.get("text"):
                        raise AgentRejected("invalid_label_section_state")
            if not raw["records"]:
                missing = list(LABEL_FIELDS)
            card = LabelCard.model_validate({"product_ref": reference, "release": result["release"],
                "records": raw["records"], "coverage": coverage, "source_snapshot_date": coverage["source_date"],
                "missing_sections": sorted(set(missing)),
                "limitations": [*coverage["limitations"],
                    "Only admitted exact product-linked labels are shown. Missing fields or absent links do not mean no warnings exist.",
                    "Stored label sections are quoted source text, not an individualized assessment or ranking of major risks."]})
        elif category == "faers":
            raw = result["evidence"]
            records = raw["records"]
            ids = [record["ingredient_id"] for record in records]
            if (len(set(ids)) != len(ids) or set(ids) != set(product.get("ingredient_ids", []))
                    or {r["ingredient_name"] for r in records} != set(product["active_ingredients"])):
                raise AgentRejected("ingredient_binding_changed")
            present = sum(record.get("analytics") is not None for record in records)
            summary = raw["summary"]
            if (summary.get("ingredient_count") != len(records)
                    or summary.get("ingredients_with_analytics") != present
                    or summary.get("ingredients_without_analytics") != len(records) - present):
                raise AgentRejected("invalid_faers_summary")
            for record in records:
                if record["coverage"].get("ingredient_id") != record["ingredient_id"]:
                    raise AgentRejected("ingredient_coverage_mismatch")
                analytics, source = record.get("analytics"), record.get("source")
                if analytics is None:
                    if record["monthly"] or record["top_reported_reactions"]:
                        raise AgentRejected("invalid_missing_analytics")
                    continue
                if not source or source.get("source_name") != "openfda_drug_event" or not source.get("source_id"):
                    raise AgentRejected("missing_source_provenance")
                _date(source.get("export_date"))
                _date(record["coverage"].get("source_date"))
                if source["export_date"] != record["coverage"]["source_date"]:
                    raise AgentRejected("source_snapshot_mismatch")
                _date(analytics.get("window_start"))
                _date(analytics.get("window_end"))
                if analytics["window_start"] > analytics["window_end"]:
                    raise AgentRejected("invalid_reporting_window")
            card = FaersCard.model_validate({"product_ref": reference, "release": result["release"],
                "records": records, "coverage": raw["coverage"], "summary": summary,
                "limitations": [FAERS_LIMITATION, *raw["coverage"]["limitations"], summary["limitation"]]})
        else:
            raise AgentRejected("incorrect_tool_name")
    except (ValidationError, KeyError, TypeError) as exc:
        raise AgentRejected("invalid_source_contract") from exc
    # A typed result cannot erase the coverage limitations needed for interpretation.
    if not card.coverage.limitations:
        raise AgentRejected("missing_source_provenance")
    return card


def card_status(card):
    if isinstance(card, LabelCard):
        if not card.records:
            return "unavailable"
        if card.missing_sections or any(r.selection_status == "EARLIER_STORED" for r in card.records):
            return "incomplete"
    if isinstance(card, FaersCard):
        if not any(r.analytics is not None for r in card.records):
            return "unavailable"
        if any(r.analytics is None or r.coverage.state != "READY" for r in card.records):
            return "incomplete"
    if card.coverage.state != "READY" or card.coverage.truncated:
        return "incomplete"
    if isinstance(card, RecallCard) and card.results_truncated:
        return "incomplete"
    return "available"


def build_briefing(public_product, requested, outcomes, routing, rag=None):
    sections, limitations, releases = [], [*LIMITATIONS,
        "Not medical advice, individualized guidance or FDA endorsement. Data is frozen, not live."], set()
    for category in TOOLS:
        if category not in requested:
            sections.append(BriefingSection(category=category, status="not_requested"))
            continue
        outcome = outcomes.get(category)
        if isinstance(outcome, str) or outcome is None:
            reason = outcome or "not_executed"
            sections.append(BriefingSection(category=category, status="failed", reason=reason))
            limitations.append(f"{category}: {reason}; this source was not verified.")
        else:
            status = card_status(outcome)
            releases.add(outcome.release.model_dump_json())
            sections.append(BriefingSection(category=category, status=status, evidence=outcome))
            limitations.extend(outcome.limitations)
            if status != "available":
                limitations.append(f"{category}: {status}; retrieved evidence does not establish comprehensive coverage.")
    if len(releases) > 1:
        raise AgentRejected("mixed_release_evidence")
    relevant = [s for s in sections if s.category in requested]
    any_evidence = any(s.evidence is not None for s in relevant)
    completed = all(s.status == "available" for s in relevant)
    status = "completed" if completed else "partial" if any_evidence else "stopped"
    if rag is not None and getattr(rag, "limitations", None):
        limitations.extend(rag.limitations)
    return ResearchBriefing(status=status, workflow_state={"completed": "COMPLETE", "partial": "PARTIAL", "stopped": "STOPPED"}[status],
        medication=MedicationIdentity.model_validate(public_product), requested_categories=list(requested),
        routing=RoutingInfo.model_validate(routing), sections=sections,
        limitations=list(dict.fromkeys(limitations)), rag=rag).model_dump()
