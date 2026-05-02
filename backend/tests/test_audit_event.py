from uuid import UUID

from app.audit.audit_event import build_audit_event


def test_build_audit_event_returns_standard_shape():
    event = build_audit_event(
        module="RecallRadar",
        source_id="openfda_drug_enforcement",
        source_name="openFDA Drug Enforcement API",
        endpoint="https://api.fda.gov/drug/enforcement.json",
        query="eye drops",
        query_params={"q": "eye drops", "limit": 5},
        retrieval_timestamp="2026-05-01T20:00:00+00:00",
        upstream_status="success",
        record_count=5,
        transform_version="recall-transform-v0.1",
        score_version="recall-risk-v0.1",
    )

    UUID(event["audit_id"])

    assert event["module"] == "RecallRadar"
    assert event["source_id"] == "openfda_drug_enforcement"
    assert event["source_name"] == "openFDA Drug Enforcement API"
    assert event["endpoint"] == "https://api.fda.gov/drug/enforcement.json"
    assert event["query"] == "eye drops"
    assert event["query_params"] == {"q": "eye drops", "limit": 5}
    assert event["retrieval_timestamp"] == "2026-05-01T20:00:00+00:00"
    assert event["upstream_status"] == "success"
    assert event["record_count"] == 5
    assert event["transform_version"] == "recall-transform-v0.1"
    assert event["score_version"] == "recall-risk-v0.1"
    assert event["disclaimer_version"] == "disclaimer-v0.1"
    assert event["error_message"] is None
    assert event["created_at"]


def test_build_audit_event_supports_error_status():
    event = build_audit_event(
        module="DrugSignal",
        source_id="openfda_drug_event",
        source_name="openFDA Drug Event API",
        endpoint="https://api.fda.gov/drug/event.json",
        query="metformin",
        query_params={"q": "metformin", "limit": 10},
        retrieval_timestamp="2026-05-01T20:00:00+00:00",
        upstream_status="error",
        record_count=0,
        transform_version="drug-event-transform-v0.1",
        error_message="openFDA unavailable",
    )

    assert event["module"] == "DrugSignal"
    assert event["upstream_status"] == "error"
    assert event["record_count"] == 0
    assert event["score_version"] is None
    assert event["error_message"] == "openFDA unavailable"