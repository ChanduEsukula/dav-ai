"""Identity-only semantic gates; regulatory evidence publication remains deferred."""
import json

from .identity import digest_rows
from .validation import validate_structure

EVIDENCE_TABLES = ("labels", "label_sections", "product_labels", "recalls", "product_recalls", "ae_summary", "ae_monthly", "ae_top_reactions", "safety_communications", "drug_communications")
MANUAL_FINISHED = {"total": 113723, "resolved": 111512, "single": 88900, "combination": 22612, "unresolved": 2211, "unresolved_KIT": 2211, "with_formulation": 111495, "with_rxcui": 83251}
MANUAL_IDENTIFIERS = {"PRODUCT_NDC": {"distinct_values": 135814}, "PACKAGE_NDC": {"distinct_values": 256491}, "RXCUI": {"distinct_values": 16495, "products_with_identifier": 83272}}


def validate_identity(connection, measurements, fixture=None, check_references=True):
    result = validate_structure(connection)
    result["scope"] = "PHASE2_IDENTITY_PRODUCT_SEARCH_ONLY; regulatory evidence and final publication not assessed"
    errors = result["errors"]
    row_checks = {}
    for table, expected in measurements["expected_sqlite_rows"].items():
        cursor = connection.execute(f"SELECT * FROM {table}")
        digest = digest_rows(list(row) for row in cursor)
        count = result["table_counts"][table]
        row_checks[table] = {"actual_rows": count, "expected_rows": expected["rows"], "actual_sha256_sorted_row_hashes": digest,
            "expected_sha256_sorted_row_hashes": expected["sha256_sorted_row_hashes"],
            "passed": count == expected["rows"] and digest == expected["sha256_sorted_row_hashes"]}
        if not row_checks[table]["passed"]:
            errors.append({"gate": "all_projected_source_fields_reconciled", "table": table})
    for table in EVIDENCE_TABLES:
        if result["table_counts"][table] != 0:
            errors.append({"gate": "no_phase3_evidence", "table": table})
    sql_checks = {
        "excluded_products_in_runtime": "SELECT count(*) FROM products WHERE eligibility_mode='EXCLUDED_V1'",
        "membership_completeness_mismatch": """SELECT count(*) FROM products p WHERE p.ingredient_set_complete != EXISTS(SELECT 1 FROM product_ingredients i WHERE i.product_id=p.product_id)
             OR p.is_combination != ((SELECT count(*) FROM product_ingredients i WHERE i.product_id=p.product_id)>1)""",
        "unresolved_product_with_formulation": "SELECT count(*) FROM products WHERE ingredient_set_complete=0 AND formulation_id IS NOT NULL",
        "unresolved_product_coverage_not_unknown": """SELECT count(*) FROM products p LEFT JOIN coverage c ON c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='identity' AND c.window_key=''
             WHERE p.ingredient_set_complete=0 AND (c.state IS NULL OR c.state!='UNKNOWN' OR c.measured_count IS NOT NULL)""",
        "unresolved_finished_human_not_kit": """SELECT count(*) FROM products WHERE ingredient_set_complete=0 AND finished=1
             AND product_type IN ('HUMAN PRESCRIPTION DRUG','HUMAN OTC DRUG') AND (dosage_form IS NULL OR dosage_form!='KIT')""",
        "normal_consumer_classification_mismatch": """SELECT count(*) FROM products WHERE (eligibility_mode='NORMAL_CONSUMER') != (consumer_classification='NORMAL_CONSUMER_HUMAN_PRODUCT')""",
        "product_without_identity_coverage": "SELECT count(*) FROM products p WHERE NOT EXISTS(SELECT 1 FROM coverage c WHERE c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='identity' AND c.window_key='')",
    }
    checks = {name: connection.execute(sql).fetchone()[0] for name, sql in sql_checks.items()}
    for name, count in checks.items():
        if count:
            errors.append({"gate": name, "violations": count})
    mismatches = []
    if check_references:
        for key, expected in MANUAL_FINISHED.items():
            actual = measurements["finished_human"].get(key, 0)
            if actual != expected:
                mismatches.append({"measurement": "finished_human." + key, "expected": expected, "actual": actual, "classification": "UNRESOLVED"})
        for kind, refs in MANUAL_IDENTIFIERS.items():
            for key, expected in refs.items():
                actual = measurements["source_identifier_counts"][kind][key]
                if actual != expected:
                    mismatches.append({"measurement": kind + "." + key, "expected": expected, "actual": actual, "classification": "UNRESOLVED"})
        if fixture:
            for key, actual in (("counts", measurements["eligibility_counts"]), ("primary_reason_counts", measurements["primary_reason_counts"]), ("combination_counts", measurements["combination_counts"])):
                if actual != fixture[key]:
                    mismatches.append({"measurement": "policy_fixture." + key, "expected": fixture[key], "actual": actual, "classification": "UNRESOLVED"})
            if measurements["normal_consumer_identity_partial"] != fixture["normal_consumer_identity_partial_flags"]["identity_partial_candidates"]:
                mismatches.append({"measurement": "policy_fixture.identity_partial", "classification": "UNRESOLVED"})
        if result["table_counts"]["ingredients"] != 7733 or result["table_counts"]["formulations"] != 34344 or measurements["source_product_count"] != 138259:
            errors.append({"gate": "pinned_identity_universe_counts"})
    errors.extend({"gate": "reference_reconciliation", **m} for m in mismatches)
    result.update({"passed": not errors, "projected_row_checks": row_checks, "identity_sql_checks": checks,
        "reference_discrepancies": mismatches, "manual_references_match": not mismatches if check_references else None})
    return result


def ambiguity_report(connection):
    identifiers = {}
    for kind in ("PRODUCT_NDC", "PACKAGE_NDC", "RXCUI"):
        groups = connection.execute("SELECT value,count(*) n FROM product_identifiers WHERE identifier_type=? GROUP BY value ORDER BY n DESC,value", (kind,)).fetchall()
        identifiers[kind] = {"distinct_values": len(groups), "association_rows": sum(r[1] for r in groups),
            "ambiguous_values": sum(r[1] > 1 for r in groups), "max_candidates": max((r[1] for r in groups), default=0),
            "examples": [{"value": r[0], "candidate_count": r[1]} for r in groups if r[1] > 1][:5]}
    names = {}
    for role in ("BRAND", "GENERIC", "BRAND_BASE"):
        groups = connection.execute("SELECT normalized_name,count(*) n FROM search_names WHERE name_role=? GROUP BY normalized_name ORDER BY n DESC,normalized_name", (role,)).fetchall()
        names[role] = {"distinct_names": len(groups), "ambiguous_names": sum(r[1] > 1 for r in groups),
            "max_candidates": max((r[1] for r in groups), default=0),
            "examples": [{"normalized_name": r[0], "candidate_count": r[1]} for r in groups if r[1] > 1][:5]}
    # Ordered relational memberships produce deterministic full-set signatures.
    sets = {pid: [] for (pid,) in connection.execute("SELECT product_id FROM products")}
    for pid, iid in connection.execute("SELECT product_id,ingredient_id FROM product_ingredients ORDER BY product_id,ingredient_id"):
        sets[pid].append(iid)
    name_sets = {}; unresolved_names = set()
    for name, pid in connection.execute("SELECT normalized_name,product_id FROM search_names WHERE entity_type='PRODUCT'"):
        if sets[pid]:
            name_sets.setdefault(name, set()).add(tuple(sets[pid]))
        else:
            unresolved_names.add(name)
    return {"runtime_identifiers": identifiers, "runtime_names": names,
        "runtime_search_names_multiple_resolved_ingredient_sets": sum(len(v) > 1 for v in name_sets.values()),
        "runtime_search_names_with_unresolved_identity": len(unresolved_names),
        "semantics": "Counts are associations to distinct source products, not commercial medicine counts. Empty unresolved sets are not resolved ingredient identities. Identifier flags use source-universe multiplicity, including offline exclusions."}
