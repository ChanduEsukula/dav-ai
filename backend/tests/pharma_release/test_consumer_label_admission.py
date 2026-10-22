"""Consumer-serving policy regressions; synthetic SQLite plus read-only controls."""
from urllib.parse import quote
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.pharma import release_repository
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository
from backend.tests.pharma_release.test_phase3_labels import (
    db as identity_db,
    build,
    raw_label,
)
from scripts.pharma_release.schema_ae import extend_ae_schema


@pytest.fixture
def serving_db(identity_db, monkeypatch):
    extend_ae_schema(identity_db)
    # This fixture owns its in-memory connection across multiple repository calls.
    from contextlib import nullcontext
    monkeypatch.setattr(release_repository, "connect_release", lambda: identity_db)
    monkeypatch.setattr(release_repository, "closing", nullcontext)
    yield identity_db


def serve(db, labels):
    build(db, labels)
    db.row_factory = sqlite3.Row
    return FrozenPharmaReleaseRepository()


@pytest.mark.parametrize("withheld", ["AMBIGUOUS", "NOT_SELECTED", "CONSUMER_FLAG"])
def test_withheld_label_cannot_reach_detail_timeline(serving_db, withheld):
    repo = serve(serving_db, [raw_label("withheld")])
    # Preserve a real schema-valid relationship while withholding consumer use.
    serving_db.execute(
        "UPDATE product_labels SET consumer_eligible=0, selection_status=?, "
        "applicability_class=? WHERE product_id='oz'",
        (
            "SELECTED_STORED" if withheld == "CONSUMER_FLAG" else "NOT_SELECTED",
            withheld if withheld == "AMBIGUOUS" else "EXACT_PRODUCT",
        ),
    )
    serving_db.commit()

    labels = repo.safety("oz")["labels"]
    assert labels["records"] == labels["latest_records"] == []
    assert labels["coverage"]["state"] == "UNKNOWN"
    assert labels["coverage"]["measured_count"] is None
    assert labels["coverage"]["stored_record_count"] == 0
    assert "does not establish" in labels["coverage"]["empty_message"]
    timeline = repo.timeline("oz")
    assert not any(e["event_type"] == "label" for e in timeline["events"])
    assert timeline["coverage"]["labels"] == labels["coverage"]


def test_independent_sets_survive_without_superseded_or_other_product_labels(serving_db):
    repo = serve(serving_db, [
        raw_label("old", set_id="shared", version="1", effective_time="20200101"),
        raw_label("selected", set_id="shared", version="2", effective_time="20210101"),
        raw_label("independent", set_id="other-set", effective_time="20220101"),
        raw_label("other-product", ndcs=["0001-02"]),
    ])
    labels = repo.safety("oz")["labels"]
    assert {r["source_record_id"] for r in labels["records"]} == {"selected", "independent"}
    assert labels["latest_records"] == labels["records"]
    assert labels["coverage"]["measured_count"] == 2
    assert labels["coverage"]["stored_record_count"] == 2
    assert {e["record_id"] for e in repo.timeline("oz")["events"]} == {
        r["id"] for r in labels["records"]
    }


def test_earlier_stored_label_is_partial_and_explicit_everywhere(serving_db):
    repo = serve(serving_db, [
        raw_label("earlier", set_id="shared", version="1"),
        raw_label("future", set_id="shared", version="2", effective_time="20270925"),
    ])
    labels = repo.safety("oz")["labels"]
    assert [r["source_record_id"] for r in labels["records"]] == ["earlier"]
    assert labels["records"][0]["selection_status"] == "EARLIER_STORED"
    assert labels["coverage"]["state"] == "PARTIAL"
    assert labels["coverage"]["stored_record_count"] == 1
    assert "Earlier stored applicable label" in repo.timeline("oz")["events"][0]["summary"]


def test_missing_structured_text_remains_unavailable(serving_db):
    repo = serve(serving_db, [raw_label("no-text", warnings_and_cautions=[], adverse_reactions=[])])
    labels = repo.safety("oz")["labels"]
    assert labels["records"] == []
    assert labels["coverage"]["state"] == "UNAVAILABLE"
    assert labels["coverage"]["measured_count"] is None


@pytest.fixture
def frozen_release():
    from app.db.pharma.release_connection import release_database_path
    if not release_database_path().is_file():
        pytest.fail("Required release artifact is not mounted; use -m 'not release_artifact' for source-only checks")
    return FrozenPharmaReleaseRepository()


@pytest.mark.release_artifact
def test_ndc_0004_0259_http_exclude_original_withheld_label(frozen_release, monkeypatch):
    products = frozen_release.search("0004-0259")
    assert products
    client = TestClient(app)
    for product in products:
        product_id = product["id"]
        url = "/api/drugs/" + quote(product_id, safe="")
        assert client.get(url).status_code == 200
        response = client.get(url + "/safety")
        assert response.status_code == 200
        labels = response.json()["labels"]
        assert labels["records"] == labels["latest_records"] == []
        assert labels["coverage"]["state"] == "UNKNOWN"
        assert labels["coverage"]["measured_count"] is None
        assert client.get(url + "/safety/labels").json()["records"] == []
        timeline = client.get(url + "/timeline").json()
        assert not any(e["event_type"] == "label" for e in timeline["events"])
        assert timeline["coverage"]["labels"] == labels["coverage"]
        # Removed Ask endpoint cannot expose withheld labels either.
        assert client.post(url + "/ask", json={"question": "warnings"}).status_code == 404


@pytest.mark.release_artifact
def test_zepbound_positive_control_has_matching_label_timeline(frozen_release):
    from backend.tests.pharma_release.test_phase5a_runtime_ask import ZEPBOUND
    labels = frozen_release.safety(ZEPBOUND)["labels"]
    assert labels["records"]
    assert all(r["selection_status"] == "SELECTED_STORED" for r in labels["records"])
    assert labels["coverage"]["state"] == "READY"
    assert labels["coverage"]["stored_record_count"] == len(labels["records"])
    assert {e["record_id"] for e in frozen_release.timeline(ZEPBOUND)["events"] if e["event_type"] == "label"} == {
        r["id"] for r in labels["records"]
    }



def test_ingredient_search_uses_membership_even_without_product_name_alias(serving_db):
    repo = serve(serving_db, [])
    ingredient = serving_db.execute(
        "SELECT i.canonical_name FROM ingredients i JOIN product_ingredients pi "
        "ON pi.ingredient_id=i.ingredient_id WHERE pi.product_id='oz' LIMIT 1"
    ).fetchone()[0]
    serving_db.execute("UPDATE search_names SET normalized_name='unrelated product alias' WHERE entity_type='PRODUCT'")
    serving_db.commit()
    rows = repo.search(ingredient)
    assert any(row['id'] == 'oz' for row in rows)
    assert all(row['consumer_classification'] for row in rows)
