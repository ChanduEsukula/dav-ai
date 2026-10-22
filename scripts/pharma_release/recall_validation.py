"""Hard manual benchmarks, exact projection and complete parent preservation."""
import json

from .identity import digest_rows
from .label_validation import PRESERVED_TABLES
from .recall_build import PROJECTION_TABLES
from .validation import validate_structure

FROZEN_TABLES = (*PRESERVED_TABLES, "labels", "label_sections", "product_labels")
UNSTARTED = ("ae_summary", "ae_monthly", "ae_top_reactions", "safety_communications", "drug_communications")
CORPUS_BENCHMARKS = {"usable_records": 17974, "HAS_EXPLICIT_TEXT_NDC": 9087, "NO_EXPLICIT_TEXT_NDC": 8887,
    "HAS_OPENFDA_NDC": 3236, "NO_OPENFDA_NDC": 14738, "TEXT_MATCHES_OPENFDA_PACKAGE": 3154, "TEXT_OPENFDA_DISAGREE": 2,
    "ALL_TEXT_NDCS_CLEAN": 3166, "MIXED_CLEAN_AND_UNMATCHED": 58, "ALL_TEXT_NDCS_UNMATCHED": 5838,
    "HAS_AMBIGUOUS_TEXT_NDC": 25, "RECALLS_WITH_AT_LEAST_ONE_CLEAN_PRODUCT": 3233,
    "RECALLS_RESOLVING_TO_ONE_PRODUCT": 3182, "RECALLS_RESOLVING_TO_MULTIPLE_PRODUCTS": 51, "TOTAL_RECALL_PRODUCT_EDGES": 3332}


def parent_fingerprints(connection):
    results = {}
    for table in (*FROZEN_TABLES, "coverage", "sources"):
        where = " WHERE domain!='recalls'" if table == "coverage" else " WHERE source_name!='openfda_drug_enforcement'" if table == "sources" else ""
        query = f"SELECT * FROM {table}" + where
        results[table] = {"rows": connection.execute(f"SELECT count(*) FROM {table}" + where).fetchone()[0],
            "sha256_sorted_row_hashes": digest_rows(list(row) for row in connection.execute(query))}
        print("Fingerprinted preserved " + table, flush=True)
    return results


def consumer_measurements(connection):
    join = "FROM product_recalls pr JOIN products p ON p.product_id=pr.product_id JOIN recalls r ON r.recall_id=pr.recall_id WHERE p.consumer_classification='NORMAL_CONSUMER_HUMAN_PRODUCT'"
    edges, recalls, products, eligible = connection.execute("SELECT count(*),count(DISTINCT pr.recall_id),count(DISTINCT pr.product_id),sum(pr.consumer_eligible) " + join).fetchone()
    return {"edges": edges, "distinct_recalls": recalls, "distinct_products": products, "consumer_eligible_edges": eligible,
        "methods": dict(connection.execute("SELECT pr.match_method,count(*) " + join + " GROUP BY pr.match_method")),
        "classification": dict(connection.execute("SELECT r.classification,count(*) " + join + " GROUP BY r.classification")),
        "reported_status": dict(connection.execute("SELECT r.source_reported_status,count(*) " + join + " GROUP BY r.source_reported_status")),
        "coverage_states": [{"classification": cls, "state": state, "products": n} for cls, state, n in connection.execute("""SELECT p.consumer_classification,c.state,count(*) FROM coverage c JOIN products p ON p.product_id=c.product_id WHERE c.domain='recalls' AND c.entity_type='PRODUCT' GROUP BY p.consumer_classification,c.state""")]}


def validate_recalls(connection, report, expected_parent=None, check_benchmarks=True):
    result = validate_structure(connection); errors = result["errors"]
    result["scope"] = "PHASE3B_PRODUCT_SCOPED_RECALLS_ONLY; AE/communications and publication not validated"
    result["consumer"] = consumer_measurements(connection)
    projections = {}
    for table in PROJECTION_TABLES:
        where = " WHERE domain='recalls'" if table == "coverage" else ""
        actual = {"projected_rows": connection.execute(f"SELECT count(*) FROM {table}" + where).fetchone()[0],
            "sha256_sorted_row_hashes": digest_rows(list(row) for row in connection.execute(f"SELECT * FROM {table}" + where))}
        expected = report["projection"][table]
        projections[table] = actual | {"passed": all(actual[k] == expected[k] for k in actual)}
        if not projections[table]["passed"]: errors.append({"gate": "exact_source_projection", "table": table})
    result["projected_row_checks"] = projections
    if expected_parent is not None:
        actual_parent = parent_fingerprints(connection)
        result["parent_preservation"] = {t: actual_parent[t] | {"passed": actual_parent[t] == expected_parent[t], "parent": expected_parent[t]} for t in expected_parent}
        for table, checked in result["parent_preservation"].items():
            if not checked["passed"]: errors.append({"gate": "frozen_parent_row_changed", "table": table})
    for table in UNSTARTED:
        if result["table_counts"][table]: errors.append({"gate": "unstarted_future_table", "table": table})
    queries = {
        "edge_not_clean_frozen_identifier": """SELECT count(*) FROM product_recalls pr WHERE (SELECT count(*) FROM product_identifiers i WHERE i.value=pr.matched_value AND i.identifier_type=CASE pr.match_method WHEN 'EXACT_PACKAGE_NDC' THEN 'PACKAGE_NDC' ELSE 'PRODUCT_NDC' END)!=1 OR NOT EXISTS(SELECT 1 FROM product_identifiers i WHERE i.product_id=pr.product_id AND i.value=pr.matched_value AND i.identifier_type=CASE pr.match_method WHEN 'EXACT_PACKAGE_NDC' THEN 'PACKAGE_NDC' ELSE 'PRODUCT_NDC' END AND i.is_unique_product=1 AND i.has_conflict=0)""",
        "edge_without_explicit_text_basis": """SELECT count(*) FROM product_recalls pr WHERE pr.match_method NOT IN ('EXACT_PACKAGE_NDC','EXACT_PRODUCT_NDC') OR json_extract(pr.verification_basis_json,'$.authority')!='EXPLICIT_RECALL_TEXT_NDC' OR NOT EXISTS(SELECT 1 FROM json_each(pr.verification_basis_json,'$.matching_occurrences') o WHERE json_extract(o.value,'$.product_id')=pr.product_id AND json_extract(o.value,'$.attempted_method')=pr.match_method AND json_extract(o.value,'$.matched_release_identifier')=pr.matched_value AND json_extract(o.value,'$.resolution')='CLEAN')""",
        "package_precedence_violation": """SELECT count(*) FROM product_recalls pr WHERE pr.match_method!='EXACT_PACKAGE_NDC' AND EXISTS(SELECT 1 FROM json_each(pr.verification_basis_json,'$.matching_occurrences') o WHERE json_extract(o.value,'$.attempted_method')='EXACT_PACKAGE_NDC')""",
        "consumer_identity_scope_failure": """SELECT count(*) FROM product_recalls pr JOIN products p ON p.product_id=pr.product_id WHERE pr.consumer_eligible=1 AND (p.consumer_classification!='NORMAL_CONSUMER_HUMAN_PRODUCT' OR p.eligibility_mode!='NORMAL_CONSUMER' OR p.ingredient_set_complete!=1 OR p.formulation_id IS NULL OR pr.explicit_scope_verified!=1 OR pr.ingredient_set_verified!=1 OR pr.formulation_scope_verified!=1 OR pr.applicability_class NOT IN ('AFFECTED_PRODUCT','AFFECTED_PACKAGE') OR json_array_length(pr.conflicts_json)!=0)""",
        "lot_text_loss_or_invented_scope": "SELECT count(*) FROM product_recalls pr JOIN recalls r ON r.recall_id=pr.recall_id WHERE pr.lot_code_text IS NOT r.code_info OR pr.lot_scope!='UNKNOWN'",
        "coverage_false_absence_or_positive_ready": """SELECT count(*) FROM coverage c WHERE c.domain='recalls' AND (c.state NOT IN ('PARTIAL','UNKNOWN') OR (c.entity_type='PRODUCT' AND ((EXISTS(SELECT 1 FROM product_recalls pr WHERE pr.product_id=c.product_id))!=(c.state='PARTIAL'))) OR (c.state='UNKNOWN' AND c.measured_count IS NOT NULL))""",
        "missing_product_recall_coverage": "SELECT count(*) FROM products p WHERE NOT EXISTS(SELECT 1 FROM coverage c WHERE c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='recalls' AND c.window_key='')",
        "missing_record_recall_coverage": "SELECT count(*) FROM recalls r WHERE NOT EXISTS(SELECT 1 FROM coverage c WHERE c.entity_type='RECALL' AND c.entity_id=r.recall_id AND c.domain='recalls' AND c.window_key='')"}
    result["semantic_checks"] = {name: connection.execute(sql).fetchone()[0] for name, sql in queries.items()}
    for name, n in result["semantic_checks"].items():
        if n: errors.append({"gate": name, "violations": n})
    benchmarks = []
    def compare(name, actual, expected):
        check = {"measurement": name, "actual": actual, "expected": expected, "passed": actual == expected}
        benchmarks.append(check)
        if not check["passed"]: errors.append({"gate": "hard_benchmark_mismatch", **check})
    if check_benchmarks:
        for name, expected in CORPUS_BENCHMARKS.items(): compare(name, report["counts"].get(name, 0), expected)
        for table, expected in {"labels": 83684, "label_sections": 502104, "product_labels": 107377, "recalls": 17974, "product_recalls": 3332}.items():
            compare("table." + table, result["table_counts"][table], expected)
        for name, expected in {"edges": 3191, "distinct_recalls": 3097, "distinct_products": 2478, "consumer_eligible_edges": 3191,
            "methods": {"EXACT_PACKAGE_NDC": 2942, "EXACT_PRODUCT_NDC": 249},
            "classification": {"Class I": 228, "Class II": 2363, "Class III": 600},
            "reported_status": {"Terminated": 1999, "Ongoing": 1089, "Completed": 103}}.items():
            compare("normal_consumer." + name, result["consumer"][name], expected)
    result["benchmarks"] = benchmarks; result["passed"] = not errors
    return result


def spot_checks(connection):
    cases = {}
    for number, expected in (("D-0321-2019", ["0378-1722-93"]), ("D-0528-2021", []), ("D-1293-2019", [])):
        row = connection.execute("SELECT recall_id,source_identity_json,product_description FROM recalls WHERE recall_number=?", (number,)).fetchone()
        edges = connection.execute("SELECT matched_value,match_method,product_id FROM product_recalls WHERE recall_id=? ORDER BY matched_value", (row[0],)).fetchall() if row else []
        cases[number] = {"passed": row is not None and [r[0] for r in edges] == expected, "edges": edges,
            "preserved_source_and_resolution": json.loads(row[1]) if row else None}
    examples = {}
    expected = {"0169-4307": ("rybelsus", "tablet"), "0338-3814": ("clindamycin", "injection, solution"),
        "0378-6322": ("valsartan", "tablet, film coated"), "67457-386": ("mycophenolate", "injection, powder, lyophilized, for solution"),
        "72572-470": ("nicardipine", "injection, solution")}
    for ndc, (name, dosage) in expected.items():
        rows = connection.execute("""SELECT p.product_id,p.brand_name,p.generic_name,p.dosage_form,p.routes_json,f.strengths_json FROM product_identifiers i JOIN products p ON p.product_id=i.product_id LEFT JOIN formulations f ON f.formulation_id=p.formulation_id WHERE i.identifier_type='PRODUCT_NDC' AND i.value=?""", (ndc,)).fetchall()
        edges = connection.execute("""SELECT r.recall_number,pr.match_method,pr.matched_value FROM product_recalls pr JOIN recalls r ON r.recall_id=pr.recall_id JOIN product_identifiers i ON i.product_id=pr.product_id WHERE i.identifier_type='PRODUCT_NDC' AND i.value=? ORDER BY r.recall_number""", (ndc,)).fetchall()
        examples[ndc] = {"passed": len(rows) == 1 and name in ((rows[0][1] or '') + ' ' + (rows[0][2] or '')).casefold() and (rows[0][3] or '').casefold() == dosage and bool(edges), "frozen_identity": rows, "recall_edges": edges}
    semaglutide = connection.execute("""SELECT p.brand_name,p.product_id,r.recall_number,pr.matched_value,pr.match_method FROM products p JOIN product_ingredients pi ON pi.product_id=p.product_id JOIN ingredients i ON i.ingredient_id=pi.ingredient_id JOIN product_recalls pr ON pr.product_id=p.product_id JOIN recalls r ON r.recall_id=pr.recall_id WHERE lower(i.canonical_name)='semaglutide' ORDER BY p.product_id,r.recall_number""").fetchall()
    return {"passed": all(x["passed"] for x in cases.values()) and all(x["passed"] for x in examples.values()),
        "scope_and_malformed_cases": cases, "known_product_corroboration": examples, "semaglutide_exact_product_edges": semaglutide,
        "specificity_basis": "Every edge must have its own explicit matched text NDC; neither ingredient membership nor openfda product families create edges. Scope validation applies equally to Rybelsus, Ozempic, Wegovy and combination products."}
