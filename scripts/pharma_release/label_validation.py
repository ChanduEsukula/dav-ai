"""Pinned strict-linkage benchmarks, exact projected text, scope and parent gates."""
from collections import Counter
import hashlib
import json

from .identity import digest_rows
from .label_build import DYNAMIC_EDGE_FIELDS, PROJECTION_TABLES
from .label_extract import FIELDS, OPTIONAL_FIELD
from .validation import validate_structure

MANUAL_SECTION_FIELDS = {"boxed_warning": 33173, "warnings_and_cautions": 47170, "warnings": 209072,
    "contraindications": 89739, "adverse_reactions": 91872, "drug_interactions": 68767, "warnings_and_precautions": 0}
STEP1_NONBLANK = {"boxed_warning": 33146, "warnings_and_cautions": 47047, "warnings": 204699,
    "contraindications": 89729, "adverse_reactions": 91861, "drug_interactions": 68722, "warnings_and_precautions": 0}
MANUAL_IDENTITY = {"product_ndc": 86314, "package_ndc": 86314, "rxcui": 64029, "spl_id": 86314,
    "spl_set_id": 86314, "application_number": 74611, "substance_name": 84722, "brand_name": 86314, "generic_name": 86314}
MANUAL_MULTIPLE = {"product_ndc": 10779, "package_ndc": 39445, "rxcui": 13964, "substance_name": 19583, "brand_name": 678, "generic_name": 169}
NORMAL_SECTIONS = {"boxed_warning": 19514, "warnings_and_cautions": 31806, "warnings": 55767,
    "contraindications": 48658, "adverse_reactions": 49801, "drug_interactions": 40300}
CLASS_LABEL_COUNTS = {"NORMAL_CONSUMER_HUMAN_PRODUCT": 89429, "SPECIAL_REGULATORY_CATEGORY_HUMAN_PRODUCT": 15860,
    "UNRESOLVED_IDENTITY": 2062, "REGULATORY_RESEARCH_ONLY": 22}
PRESERVED_TABLES = ("ingredients", "products", "formulations", "product_ingredients", "product_identifiers", "search_names")
UNTREATED = ("recalls", "product_recalls", "ae_summary", "ae_monthly", "ae_top_reactions", "safety_communications", "drug_communications")


def coverage_measurements(connection):
    by_class = {}
    for cls, total in connection.execute("SELECT consumer_classification,count(*) FROM products GROUP BY consumer_classification"):
        labeled = connection.execute("SELECT count(DISTINCT p.product_id) FROM products p JOIN product_labels pl ON pl.product_id=p.product_id WHERE p.consumer_classification=?", (cls,)).fetchone()[0]
        by_class[cls] = {"total": total, "with_clean_label": labeled, "without_clean_label": total - labeled, "percent_with_clean_label": 100 * labeled / total}
    normal_clause = "p.consumer_classification='NORMAL_CONSUMER_HUMAN_PRODUCT'"
    sections = {}
    for field in FIELDS:
        counts = connection.execute(f"""SELECT count(DISTINCT CASE WHEN s.field_present=1 THEN p.product_id END),
            count(DISTINCT CASE WHEN s.state='READY' THEN p.product_id END)
            FROM products p JOIN product_labels pl ON pl.product_id=p.product_id JOIN label_sections s ON s.label_id=pl.label_id
            WHERE {normal_clause} AND s.source_field=?""", (field,)).fetchone()
        sections[field] = {"source_field_present_products": counts[0], "nonblank_usable_text_products": counts[1],
            "percent_of_labeled_field_present": 100 * counts[0] / by_class["NORMAL_CONSUMER_HUMAN_PRODUCT"]["with_clean_label"],
            "percent_of_all_normal_field_present": 100 * counts[0] / by_class["NORMAL_CONSUMER_HUMAN_PRODUCT"]["total"]}
    any_counts = connection.execute(f"""SELECT count(DISTINCT CASE WHEN s.field_present=1 THEN p.product_id END),
        count(DISTINCT CASE WHEN s.state='READY' THEN p.product_id END) FROM products p JOIN product_labels pl ON pl.product_id=p.product_id
        JOIN label_sections s ON s.label_id=pl.label_id WHERE {normal_clause} AND s.source_field IN ({','.join('?' for _ in FIELDS)})""", FIELDS).fetchone()
    per_product = connection.execute("SELECT count(*) n FROM product_labels GROUP BY product_id").fetchall()
    normal_hist = connection.execute(f"SELECT count(*) n FROM product_labels pl JOIN products p ON p.product_id=pl.product_id WHERE {normal_clause} GROUP BY pl.product_id").fetchall()
    states = [{"classification": cls, "state": state, "products": n} for cls, state, n in connection.execute("""SELECT p.consumer_classification,c.state,count(*) FROM products p
        JOIN coverage c ON c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='labels' AND c.window_key=''
        GROUP BY p.consumer_classification,c.state""")]
    consumer = connection.execute(f"SELECT count(DISTINCT p.product_id),count(*) FROM product_labels pl JOIN products p ON p.product_id=pl.product_id WHERE {normal_clause} AND pl.consumer_eligible=1").fetchone()
    return {"classifications": by_class, "normal_section_products": sections,
        "normal_products_any_requested_field_present": any_counts[0], "normal_products_any_nonblank_usable_section": any_counts[1],
        "products_with_clean_label": len(per_product), "labels_per_product": dict(Counter(str(r[0]) for r in per_product)),
        "normal_labels_per_product": dict(Counter(str(r[0]) for r in normal_hist)), "domain_coverage_states": states,
        "normal_products_with_consumer_eligible_selected_label": consumer[0], "consumer_eligible_edges": consumer[1],
        "semantics": "Clean-label coverage measures strict source-product NDC linkage, not clinical completeness or consumer selection readiness. Field presence and nonblank usable text are separate; neither missing field nor UNKNOWN/UNAVAILABLE establishes medical absence."}


def projected_checks(connection, projection):
    result = {}
    for table in PROJECTION_TABLES:
        columns = [r[1] for r in connection.execute(f"PRAGMA table_info({table})") if table != "product_labels" or r[1] not in DYNAMIC_EDGE_FIELDS]
        actual_hash = digest_rows(list(row) for row in connection.execute(f"SELECT {','.join(columns)} FROM {table}"))
        count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        expected = projection[table]
        result[table] = {"rows": count, "expected_rows": expected["projected_rows"], "sha256_sorted_row_hashes": actual_hash,
            "expected_sha256_sorted_row_hashes": expected["sha256_sorted_row_hashes"],
            "passed": count == expected["projected_rows"] and actual_hash == expected["sha256_sorted_row_hashes"]}
    return result


def parent_checks(connection, parent_validation):
    result = {}
    for table in (*PRESERVED_TABLES, "coverage"):
        where = " WHERE domain='identity'" if table == "coverage" else ""
        cursor = connection.execute(f"SELECT * FROM {table}" + where)
        actual = digest_rows(list(row) for row in cursor)
        count = connection.execute(f"SELECT count(*) FROM {table}" + where).fetchone()[0]
        expected = parent_validation["projected_row_checks"][table]
        result[table] = {"rows": count, "sha256_sorted_row_hashes": actual,
            "passed": count == expected["actual_rows"] and actual == expected["actual_sha256_sorted_row_hashes"]}
    return result


def validate_labels(connection, report, coverage, parent_validation=None, check_benchmarks=True):
    result = validate_structure(connection); errors = result["errors"]
    result["scope"] = "PHASE3A_LABELS_ONLY; recalls/AE/communications and publication not validated"
    projections = projected_checks(connection, report["projection"])
    for table, check in projections.items():
        if not check["passed"]: errors.append({"gate": "exact_source_projection", "table": table})
    parents = parent_checks(connection, parent_validation) if parent_validation else {}
    for table, check in parents.items():
        if not check["passed"]: errors.append({"gate": "parent_identity_preservation", "table": table})
    for table in UNTREATED:
        if result["table_counts"][table]: errors.append({"gate": "unstarted_evidence_table", "table": table})
    semantic_queries = {
        "label_missing_required_section_slots": """SELECT count(*) FROM labels l WHERE
            (SELECT count(*) FROM label_sections s WHERE s.label_id=l.label_id AND s.source_field!='warnings_and_precautions')!=6""",
        "manufactured_precautions_slot": "SELECT count(*) FROM label_sections WHERE source_field='warnings_and_precautions' AND field_present=0",
        "consumer_edge_on_regulatory_product": """SELECT count(*) FROM product_labels pl JOIN products p ON p.product_id=pl.product_id
            WHERE pl.consumer_eligible=1 AND p.eligibility_mode!='NORMAL_CONSUMER'""",
        "consumer_edge_document_or_scope_failure": """SELECT count(*) FROM product_labels pl JOIN labels l ON l.label_id=pl.label_id
            WHERE pl.consumer_eligible=1 AND (pl.applicability_class!='EXACT_PRODUCT' OR pl.ingredient_set_verified!=1 OR pl.formulation_scope_verified!=1
            OR pl.selection_status NOT IN ('SELECTED_STORED','EARLIER_STORED') OR l.date_status!='VALID' OR l.version_number IS NULL
            OR l.has_requested_safety_section!=1 OR l.extraction_valid!=1 OR json_array_length(pl.conflicts_json)>0)""",
        "label_ready_section_not_nonblank": "SELECT count(*) FROM label_sections WHERE state='READY' AND (full_text IS NULL OR length(trim(full_text))=0)",
        "labels_without_product_edges": "SELECT count(*) FROM labels l WHERE NOT EXISTS(SELECT 1 FROM product_labels pl WHERE pl.label_id=l.label_id)",
        "product_label_not_strict_flag_matched": """SELECT count(*) FROM product_labels pl WHERE NOT EXISTS(
            SELECT 1 FROM product_identifiers i WHERE i.product_id=pl.product_id AND i.identifier_type='PRODUCT_NDC' AND i.value=pl.matched_value AND i.is_unique_product=1 AND i.has_conflict=0)""",
        "label_with_any_referenced_ndc_failing_strict_rule": """SELECT count(*) FROM labels l WHERE EXISTS(
            SELECT 1 FROM json_each(l.source_identity_json,'$.product_ndc') n WHERE
            (SELECT count(*) FROM product_identifiers i WHERE i.identifier_type='PRODUCT_NDC' AND i.value=n.value)!=1 OR
            NOT EXISTS(SELECT 1 FROM product_identifiers i WHERE i.identifier_type='PRODUCT_NDC' AND i.value=n.value AND i.is_unique_product=1 AND i.has_conflict=0))""",
        "missing_product_label_coverage": """SELECT count(*) FROM products p WHERE NOT EXISTS(SELECT 1 FROM coverage c
            WHERE c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='labels' AND c.window_key='')""",
    }
    checks = {k: connection.execute(v).fetchone()[0] for k, v in semantic_queries.items()}
    for name, count in checks.items():
        if count: errors.append({"gate": name, "violations": count})
    benchmarks = []
    def compare(name, actual, expected):
        check = {"measurement": name, "actual": actual, "expected": expected, "passed": actual == expected}
        benchmarks.append(check)
        if not check["passed"]: errors.append({"gate": "manual_benchmark_mismatch", **check})
    if check_benchmarks:
        c = report["counts"]
        for name, expected in {"source_labels": 262887, "with_product_ndc": 86314, "clean_labels": 83684, "clean_edges": 107377,
            "primary_NO_PRODUCT_NDC": 176573, "with_any_matching_ndc": 86302, "all_ndcs_matched_regardless_flags": 85713,
            "no_matching_product_ndc": 12, "naive_exactly_one_candidate": 74311, "naive_multiple_candidates": 11991}.items():
            compare(name, c.get(name, 0), expected)
        compare("strict_rejected_ndc_labels", c.get("primary_AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC", 0) + c.get("primary_UNMATCHED_PRODUCT_NDC", 0), 2630)
        for field, expected in MANUAL_SECTION_FIELDS.items(): compare("source_field_presence." + field, report["section_field_presence"].get(field, 0), expected)
        for field, expected in STEP1_NONBLANK.items(): compare("step1_nonblank." + field, report["section_nonblank_text"].get(field, 0), expected)
        for field, expected in MANUAL_IDENTITY.items(): compare("identity_fields." + field, report["identity_field_presence"].get(field, 0), expected)
        for field, expected in MANUAL_MULTIPLE.items(): compare("identity_multi." + field, report["identity_multi_valued"].get(field, 0), expected)
        for name, expected in {"distinct_label_product_ndcs": 111425, "distinct_matched_product_ndcs": 110391, "distinct_unmatched_product_ndcs": 1034,
            "distinct_runtime_ambiguous_product_ndcs": 863, "no_ndc_set_ids_shared_with_identified_labels": 0, "no_ndc_set_ids_not_unique": 0}.items(): compare(name, report[name], expected)
        compare("no_ndc_nonempty_openfda", c.get("no_ndc_nonempty_openfda", 0), 0)
        compare("products_with_clean_label", coverage["products_with_clean_label"], 107373)
        compare("all_labels_per_product", coverage["labels_per_product"], {"1": 107369, "2": 4})
        compare("normal_labels_per_product", coverage["normal_labels_per_product"], {"1": 89425, "2": 4})
        for cls, expected in CLASS_LABEL_COUNTS.items(): compare("class_labeled." + cls, coverage["classifications"][cls]["with_clean_label"], expected)
        compare("normal_total", coverage["classifications"]["NORMAL_CONSUMER_HUMAN_PRODUCT"]["total"], 95426)
        compare("normal_without_clean_label", coverage["classifications"]["NORMAL_CONSUMER_HUMAN_PRODUCT"]["without_clean_label"], 5997)
        for field, expected in NORMAL_SECTIONS.items(): compare("normal_source_field_present." + field, coverage["normal_section_products"][field]["source_field_present_products"], expected)
        compare("normal_any_requested_field", coverage["normal_products_any_requested_field_present"], 88281)
    result.update({"passed": not errors, "projection_checks": projections, "parent_identity_checks": parents,
        "semantic_sql_checks": checks, "manual_benchmarks": benchmarks, "all_manual_benchmarks_pass": all(b["passed"] for b in benchmarks) if check_benchmarks else None})
    return result
