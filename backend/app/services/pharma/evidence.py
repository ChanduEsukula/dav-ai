"""One frozen-release evidence contract shared by the explorer and PDF renderer."""
from contextlib import closing
from urllib.parse import urlsplit

from app.db.pharma.release_connection import connect_release
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository

LIMITATIONS = [
    "Missing linked recalls do not establish that a drug has never been recalled. Recall coverage is partial.",
    "Adverse-event counts are ingredient-level reporting associations, not product-specific counts, incidence, causality, comparative safety, or personal risk.",
    "Spontaneous reporting can be incomplete, duplicated, biased, and revised. Reports do not establish that the medication caused a reaction.",
    "Ingredient counts must not be summed into a product total, including for combination products.",
    "Name and age identify the report only. This report provides no diagnosis, treatment recommendation, or age-specific risk estimate.",
]


def official_source(url):
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        if (parsed.scheme == "https" and parsed.hostname in {
            "api.fda.gov", "www.fda.gov", "fda.gov", "open.fda.gov",
            "download.open.fda.gov",
        } and not parsed.username and not parsed.password and parsed.port in (None, 443)):
            return url
    except ValueError:
        pass
    return None


def release_metadata():
    with closing(connect_release()) as con:
        row = dict(con.execute("SELECT * FROM release_manifest").fetchone())
        # Expose source dates/URLs, never local archive paths from raw manifest JSON.
        keys = ("release_id", "contract_id", "policy_version", "schema_version", "build_version",
                "build_time_utc", "ndc_observation_date", "label_export_date", "window_start", "window_end")
        return {
            **{k: row[k] for k in keys},
            "publication_authorized": False,
            "sources": [dict(s) for s in con.execute(
                "SELECT source_id, source_name, source_url, export_date, observed_at "
                "FROM sources ORDER BY source_name, source_id"
            )],
            "limitations": LIMITATIONS,
        }


def drug_evidence(product_id, repository=None):
    repo = repository or FrozenPharmaReleaseRepository()
    drug = repo.find_by_id(product_id)
    if drug is None:
        return None
    safety = repo.safety(product_id)
    return {
        "drug": drug,
        "recalls": safety["recalls"],
        "adverse_events": safety["adverse_events"],
        "release": release_metadata(),
        "limitations": LIMITATIONS,
    }
