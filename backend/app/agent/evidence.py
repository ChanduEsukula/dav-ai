"""Deterministic evidence only. Never synthesize recall/lot/causality assertions."""
from copy import deepcopy
from datetime import date

from app.agent.contracts import AgentRejected
from app.services.pharma.evidence import LIMITATIONS, official_source


def evidence_card(reference, public_product, product, result):
    if (not isinstance(result, dict) or result.get("status") not in {"found", "no_linked_recalls"}
            or result.get("product_id") != product["product_id"]
            or result.get("product_ndcs") != product["product_ndcs"]):
        raise AgentRejected("evidence_unavailable")
    coverage = result.get("coverage")
    if (not isinstance(coverage, dict) or coverage.get("state") not in {"PARTIAL", "READY", "UNKNOWN", "UNAVAILABLE"}
            or not isinstance(coverage.get("limitations"), list) or not coverage["limitations"]):
        raise AgentRejected("missing_source_provenance")
    snapshot = result.get("source_snapshot_date")
    try:
        date.fromisoformat(snapshot)
    except (TypeError, ValueError):
        raise AgentRejected("missing_source_provenance") from None
    records = result.get("records")
    if not isinstance(records, list) or bool(records) != (result["status"] == "found"):
        raise AgentRejected("evidence_unavailable")
    for record in records:
        if (not isinstance(record, dict) or any(not record.get(k) for k in (
                "id", "recall_number", "classification", "reason_for_recall", "source_record_id"))
                or not official_source(record.get("source_url"))):
            raise AgentRejected("missing_source_provenance")
        applicability = record.get("applicability_class")
        if applicability == "AFFECTED_PACKAGE":
            matched = record.get("match_method") == "EXACT_PACKAGE_NDC" and record.get("matched_value") in product["package_ndcs"]
        elif applicability == "AFFECTED_PRODUCT":
            matched = record.get("match_method") == "EXACT_PRODUCT_NDC" and record.get("matched_value") in product["product_ndcs"]
        else:
            matched = False
        if not matched:
            raise AgentRejected("unsupported_recall_applicability")
        if record.get("lot_scope") not in {"UNKNOWN", "EXPLICIT_RESTRICTION", "EXPLICIT_ALL_LOTS"}:
            raise AgentRejected("unsupported_lot_scope")
        if record["lot_scope"] != "UNKNOWN" and not record.get("lot_information"):
            raise AgentRejected("unsupported_lot_scope")
    return {"type": "historical_recall_evidence", "product_ref": reference,
            "product": deepcopy(public_product), "records": deepcopy(records),
            "coverage": deepcopy(coverage), "source_snapshot_date": snapshot,
            "record_count": result.get("record_count"), "returned_count": len(records),
            "results_truncated": result.get("results_truncated"),
            "limitations": [result["limitation"], *LIMITATIONS],
            "interpretation": "Historical links only. Lot applicability is not inferred; partial coverage cannot establish no historical recalls."}
