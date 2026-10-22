"""Frozen-release regressions retained after removing the Ask interface."""
from pathlib import Path
import pytest
from app.db.pharma.release_connection import release_database_path
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository

pytestmark = pytest.mark.release_artifact

ZEPBOUND = (
    'product:["openfda_ndc_directory",'
    '"0002-0152_a5dba1a3-f7f7-4b8d-b9f1-a09dcdc1b2fc"]'
)

OZEMPIC = (
    'product:["openfda_ndc_directory",'
    '"0169-4130_5e1477c5-c1b8-4fc5-af2a-83e5d356a77d"]'
)

STERILE_DILUENT = (
    'product:["openfda_ndc_directory",'
    '"0002-0800_03be5386-187a-420f-9021-55778a73eba0"]'
)

SEMAGLUTIDE = "ingredient:aceb6dacee359207f1939f8b"



@pytest.fixture(scope="module")
def release():
    if not Path(release_database_path()).is_file():
        pytest.fail("Required release artifact is not mounted; use -m 'not release_artifact' for source-only checks")
    return FrozenPharmaReleaseRepository()


def test_zepbound_exact_label_evidence(release):
    labels = release.safety(ZEPBOUND)["labels"]
    assert len(labels["records"]) == 1
    assert labels["coverage"]["state"] == "READY"
    assert all(r["source_record_id"] == "a5dba1a3-f7f7-4b8d-b9f1-a09dcdc1b2fc" for r in labels["records"])


def test_missing_recall_and_ae_remain_unknown(release):
    result = release.safety(ZEPBOUND)
    for section in ("recalls", "adverse_events"):
        assert result[section]["coverage"]["state"] == "UNKNOWN"
        assert result[section]["coverage"]["measured_count"] is None


def test_semaglutide_ingredient_analytics_and_months(release):
    result = release.safety(OZEMPIC)["adverse_events"]
    assert result["summary"]["product_report_total"] is None
    assert result["records"][0]["scope"] == "INGREDIENT"
    assert result["records"][0]["analytics"]["report_count"] > 0
    assert result["records"][0]["monthly"]
    assert result["records"][0]["top_reported_reactions"]


def test_verified_recall_keeps_partial_coverage(release):
    result = release.safety(STERILE_DILUENT)["recalls"]
    assert result["records"][0]["source_record_id"] == "D-0445-2024"
    assert result["records"][0]["reported_status"] == "Completed"
    assert result["coverage"]["state"] == "PARTIAL"
