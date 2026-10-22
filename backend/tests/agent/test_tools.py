from copy import deepcopy

import pytest

from app.agent.tools import resolve_drug_product, search_historical_recalls


def product(identifier="one", *, ndc="0009-0029", strength=".25 mg/1", name="Xanax"):
    return {"product_id": 'product:["test","' + identifier + '"]', "brand_names": [name],
            "generic_name": "alprazolam", "strength": strength, "dosage_form": "TABLET",
            "formulation_id": "formulation-" + identifier, "product_ndcs": [ndc],
            "package_ndcs": [ndc + "-01"], "active_ingredients": ["alprazolam"], "routes": ["ORAL"],
            "provenance": {"source_record_id": identifier, "source_url": "https://api.fda.gov/drug/ndc.json",
                           "observed_at": "2026-09-26"}}


def recall_result(p):
    return {"recalls": {"records": [{"id": "stored-recall", "recall_number": "D-TEST-2016",
        "classification": "Class II", "reported_status": "Terminated", "reason_for_recall": "Subpotent Drug",
        "recalling_firm": "Firm", "recall_initiation_date": "2015-09-24", "report_date": "2016-01-01",
        "lot_information": "Lot C111054", "lot_scope": "UNKNOWN", "applicability_class": "AFFECTED_PACKAGE",
        "match_method": "EXACT_PACKAGE_NDC", "matched_value": p["package_ndcs"][0],
        "source_record_id": "D-TEST-2016", "source_url": "https://api.fda.gov/drug/enforcement.json"}],
        "coverage": {"state": "PARTIAL", "source_date": "2026-09-25", "limitations": ["Partial historical coverage."]}}}


class Repository:
    def __init__(self, products=None):
        self.products = products if products is not None else [product()]
        self.queries = []
        self.safety_result = recall_result(self.products[0]) if self.products else None

    def search(self, query, *, limit):
        self.queries.append((query, limit))
        return deepcopy(self.products[:limit])

    def find_by_id(self, identifier):
        return next((deepcopy(p) for p in self.products if p["product_id"] == identifier), None)

    def safety(self, identifier):
        return deepcopy(self.safety_result)


@pytest.mark.parametrize("query", ["", " ", None, 123, "x" * 201])
def test_invalid_queries_do_not_search(query):
    repo = Repository()
    assert resolve_drug_product(query, repo)["status"] == "invalid_query"
    assert repo.queries == []


def test_exact_ndc_delegates_existing_repository_matching():
    repo = Repository()
    result = resolve_drug_product("0009-0029", repo)
    assert repo.queries == [("0009-0029", 100)]
    assert result["status"] == "resolved"
    assert result["candidates"][0]["formulation_id"] == "formulation-one"


@pytest.mark.parametrize("query", ["Xanax", "Xanax 0.25 mg"])
def test_identical_strength_different_ndcs_requires_clarification(query):
    result = resolve_drug_product(query, Repository([product(), product("two", ndc="9999-0001")]))
    assert result["status"] == "needs_clarification"
    assert len(result["candidates"]) == 2


def test_release_formulations_never_combined():
    repo = Repository([product(), product("xr", name="Xanax XR", ndc="9999-0001")])
    result = resolve_drug_product("alprazolam 0.25 mg", repo)
    assert len(result["candidates"]) == 2
    assert result["candidates"][0]["formulation_id"] != result["candidates"][1]["formulation_id"]


def test_strength_filter_retains_original_truncation_and_ambiguity():
    repo = Repository([product()] + [product(str(n), strength="1 mg/1") for n in range(99)])
    result = resolve_drug_product("Xanax .25 mg", repo)
    assert len(result["candidates"]) == 1
    assert result["results_may_be_incomplete"] is True
    assert result["status"] == "needs_clarification"


@pytest.mark.parametrize("strength", [".25 mg/5 mL", ".25 mg/0.5 mL", ".25 mg/1; 1 mg/1", "unknown"])
def test_strength_shorthand_does_not_convert_concentrations_or_combinations(strength):
    assert resolve_drug_product("Xanax .25 mg", Repository([product(strength=strength)]))["status"] == "not_found"


def test_missing_products():
    assert resolve_drug_product("missing", Repository([]))["status"] == "not_found"


@pytest.mark.parametrize("identifier", [None, "", "x" * 301, "one", "0009-0029_f5323eac"])
def test_invalid_or_incomplete_ids_never_return_evidence(identifier):
    assert search_historical_recalls(identifier, Repository())["records"] == []


@pytest.mark.parametrize("safety", [None, {}, {"recalls": None}, {"recalls": {"records": None}}, {"recalls": {"records": [None]}}])
def test_missing_evidence(safety):
    repo = Repository()
    repo.safety_result = safety
    assert search_historical_recalls(repo.products[0]["product_id"], repo)["status"] == "evidence_unavailable"


def test_fields_snapshot_and_record_truncation_preserved():
    repo = Repository()
    repo.safety_result["recalls"]["records"] *= 11
    result = search_historical_recalls(repo.products[0]["product_id"], repo)
    assert result["source_snapshot_date"] == "2026-09-25"
    assert result["record_count"] == 11 and result["returned_count"] == 10
    assert result["results_truncated"] is True
    record = result["records"][0]
    assert record["lot_scope"] == "UNKNOWN"
    assert record["applicability_class"] == "AFFECTED_PACKAGE"
    assert record["match_method"] == "EXACT_PACKAGE_NDC"
    assert record["source_record_id"] == "D-TEST-2016"


def test_explicit_extended_release_query_keeps_release_name_in_repository_search():
    repo = Repository([product("xr", name="Xanax XR", ndc="9999-0001")])
    result = resolve_drug_product("Xanax XR .25 mg", repo)
    assert repo.queries == [("Xanax XR", 100)]
    assert result["candidates"][0]["brand_names"] == ["Xanax XR"]
