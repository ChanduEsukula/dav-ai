"""Read-only adapters; reuse sealed repository selection/aggregates unchanged."""
from contextlib import closing
from copy import deepcopy

from app.agent.contracts import AgentRejected
from app.agent.research_contracts import ReleaseInfo
from app.agent.tools import search_historical_recalls
from app.db.pharma.release_connection import connect_release
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository
from app.services.pharma.evidence import release_metadata


def faers_sources(product_id):
    # Provenance only. Never recompute, deduplicate or aggregate FAERS observations.
    with closing(connect_release()) as con:
        rows = con.execute(
            "SELECT a.ingredient_id, s.source_id, s.source_name, s.source_url, s.export_date, s.observed_at "
            "FROM product_ingredients pi JOIN ae_summary a ON a.ingredient_id=pi.ingredient_id "
            "LEFT JOIN sources s ON s.source_id=a.source_id WHERE pi.product_id=?", (product_id,)
        ).fetchall()
    return {row["ingredient_id"]: {k: row[k] for k in (
        "source_id", "source_name", "source_url", "export_date", "observed_at")} for row in rows}


def get_source_evidence(category, product_id, *, repository=None, metadata_provider=release_metadata,
                        provenance_provider=faers_sources):
    repo = repository or FrozenPharmaReleaseRepository()
    product = repo.find_by_id(product_id)
    if product is None:
        raise AgentRejected("product_not_found")
    metadata = metadata_provider()
    release = ReleaseInfo.model_validate({key: metadata[key] for key in ReleaseInfo.model_fields}).model_dump()
    if category == "recalls":
        result = search_historical_recalls(product_id, repo)
    else:
        safety = repo.safety(product_id)
        key = {"labels": "labels", "faers": "adverse_events"}.get(category)
        if key is None or not isinstance(safety, dict) or not isinstance(safety.get(key), dict):
            raise AgentRejected("evidence_unavailable")
        result = {"product_id": product_id, "product_ndcs": product["product_ndcs"],
                  "evidence": deepcopy(safety[key])}
        if category == "labels":
            # Compatibility alias repeats the same admitted records; preserve the
            # canonical records once rather than tripling long source text.
            result["evidence"].pop("latest_records", None)
        if category == "faers":
            sources = provenance_provider(product_id)
            for record in result["evidence"]["records"]:
                record["source"] = sources.get(record["ingredient_id"])
    return {**result, "release": release}


def get_drug_label_evidence(product_id, **kwargs):
    """Internal exact-ID adapter; model-facing arguments contain only product_ref."""
    return get_source_evidence("labels", product_id, **kwargs)


def get_faers_reporting_evidence(product_id, **kwargs):
    return get_source_evidence("faers", product_id, **kwargs)
