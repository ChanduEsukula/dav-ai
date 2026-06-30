from copy import deepcopy

from app.services.search_workflows.source_health_contract import (
    validate_real_world_source_health_contract,
)


def _valid_body():
    return {
        "retrieval_timestamp": "2026-06-30T19:00:00Z",
        "sources_checked": [
            {
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "source_type": "live official API",
                "source_url": "https://www.saferproducts.gov/RestWebServices/Recall",
                "source_kind": "structured_api",
                "upstream_status": "success",
                "record_count": 1,
            }
        ],
        "sources_failed": [
            {
                "source_id": "fda_recalls_market_withdrawals_safety_alerts",
                "source_name": "FDA Recalls, Market Withdrawals & Safety Alerts",
                "source_type": "live official public page",
                "source_url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
                "source_kind": "public_notice",
                "error_type": "upstream_unavailable",
                "reason": "Temporary upstream source issue.",
            }
        ],
        "source_audits": [
            {
                "audit_id": "audit-cpsc",
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "module": "RealWorldSafety",
                "upstream_status": "success",
                "record_count": 1,
                "transform_version": "real-world-safety-v0.1",
                "source_snapshot_status": "stored",
                "source_pull_id": "pull-cpsc",
                "source_payload_hash": "hash-cpsc",
            }
        ],
        "source_freshness": [
            {
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "source_type": "live official API",
                "source_kind": "structured_api",
                "upstream_status": "success",
                "record_count": 1,
                "freshness_status": "pulled_and_stored",
                "user_label": "Pulled and stored",
                "explanation": "DavAI checked this public source and stored audit metadata.",
                "source_snapshot_status": "stored",
                "source_pull_id": "pull-cpsc",
                "source_payload_hash": "hash-cpsc",
                "checked_at": "2026-06-30T19:00:00Z",
            },
            {
                "source_id": "fda_recalls_market_withdrawals_safety_alerts",
                "source_name": "FDA Recalls, Market Withdrawals & Safety Alerts",
                "source_type": "live official public page",
                "source_kind": "public_notice",
                "upstream_status": "error",
                "record_count": 0,
                "freshness_status": "source_issue_reported",
                "user_label": "Source issue reported",
                "explanation": "Temporary upstream source issue.",
                "source_snapshot_status": None,
                "source_pull_id": None,
                "source_payload_hash": None,
                "checked_at": "2026-06-30T19:00:00Z",
            },
        ],
    }


def test_source_health_contract_accepts_valid_payload():
    assert validate_real_world_source_health_contract(_valid_body()) == []


def test_source_health_contract_requires_checked_source_identity_fields():
    body = _valid_body()
    body["sources_checked"][0]["source_name"] = ""

    errors = validate_real_world_source_health_contract(body)

    assert "sources_checked[0].source_name is required" in errors


def test_source_health_contract_rejects_unknown_source_kind():
    body = _valid_body()
    body["sources_failed"][0]["source_kind"] = "spreadsheet"

    errors = validate_real_world_source_health_contract(body)

    assert any("sources_failed[0].source_kind must be one of" in error for error in errors)


def test_source_health_contract_requires_freshness_for_checked_and_failed_sources():
    body = _valid_body()
    body["source_freshness"] = body["source_freshness"][:1]

    errors = validate_real_world_source_health_contract(body)

    assert any("source_freshness source_ids must match" in error for error in errors)
    assert "fda_recalls_market_withdrawals_safety_alerts" in errors[0]


def test_source_health_contract_requires_freshness_checked_at_to_match_retrieval_time():
    body = _valid_body()
    body["source_freshness"][0]["checked_at"] = "2026-06-30T20:00:00Z"

    errors = validate_real_world_source_health_contract(body)

    assert "source_freshness[0].checked_at must match retrieval_timestamp" in errors


def test_source_health_contract_rejects_negative_record_count():
    body = _valid_body()
    body["source_audits"][0]["record_count"] = -1

    errors = validate_real_world_source_health_contract(body)

    assert "source_audits[0].record_count must be a non-negative integer" in errors


def test_source_health_contract_requires_at_least_one_source():
    body = deepcopy(_valid_body())
    body["sources_checked"] = []
    body["sources_failed"] = []
    body["source_freshness"] = []

    errors = validate_real_world_source_health_contract(body)

    assert "expected at least one checked or failed source" in errors
