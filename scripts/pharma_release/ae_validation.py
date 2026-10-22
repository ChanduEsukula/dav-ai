"""AE hard gates, report/month reconciliation and untouched parent rows."""
import json

from .ae_build import PROJECTION_TABLES, product_coverage
from .ae_derive import FLAGS, WINDOW_KEY
from .identity import digest_rows
from .recall_validation import FROZEN_TABLES
from .validation import validate_structure

PRESERVED = (*FROZEN_TABLES, "recalls", "product_recalls")
UNSTARTED = ("safety_communications", "drug_communications")
SPOT_EXPECTED = {
    "ingredient:aceb6dacee359207f1939f8b": {"report_count": 27585, "unique_case_count": 27585, "serious_report_count": 14624,
        "serious_known_report_count": 27574, "death_report_count": 343, "hospitalization_report_count": 5206,
        "disability_report_count": 638, "life_threatening_report_count": 824, "reaction_term_count": 4264, "co_report_activity": 97481},
    "ingredient:377df00b1c296114c6f14396": {"report_count": 136887, "unique_case_count": 136887, "serious_report_count": 94720,
        "serious_known_report_count": 136680, "death_report_count": 23978, "hospitalization_report_count": 40761,
        "disability_report_count": 1477, "life_threatening_report_count": 3978},
    "ingredient:441bc6caee06a4e50a609d0c": {"report_count": 5794, "unique_case_count": 5794, "serious_report_count": 994,
        "serious_known_report_count": 5788, "death_report_count": 103, "hospitalization_report_count": 296,
        "disability_report_count": 19, "life_threatening_report_count": 38}}
IDENTITY_PAIR_EXPECTED = {
    "ingredient:08e4d178e1c91d6fee3988ae": ("atorvastatin calcium trihydrate", 808254),
    "ingredient:571df48520049f0e498f56f7": ("atorvastatin calcium propylene glycol solvate", 502),
    "ingredient:ef4358d0ed7580bbbb95eb89": ("metformin hydrochloride", 645827)}
EXTRA_MONTHS = [["ingredient:b890fa00e727e14f7e479fd1", "2023-09-01"], ["ingredient:f5eca3c6ff2d9c726437dcdc", "2023-09-01"]]


def parent_fingerprints(connection):
    result = {}
    for table in (*PRESERVED, "coverage", "sources"):
        where = " WHERE domain!='ae_analytics'" if table == "coverage" else " WHERE source_name!='openfda_drug_event'" if table == "sources" else ""
        result[table] = {"rows": connection.execute(f"SELECT count(*) FROM {table}" + where).fetchone()[0],
            "sha256_sorted_row_hashes": digest_rows(list(row) for row in connection.execute(f"SELECT * FROM {table}" + where))}
        print("Fingerprinted preserved " + table, flush=True)
    return result


def summary_record(connection, iid):
    cursor = connection.execute("SELECT * FROM ae_summary WHERE ingredient_id=?", (iid,)); row = cursor.fetchone()
    return dict(zip([field[0] for field in cursor.description], row)) if row else None


def spot_checks(connection):
    spots = {}
    for iid, expected in SPOT_EXPECTED.items():
        row = summary_record(connection, iid)
        spots[iid] = {"passed": row is not None and all(row[field] == value for field, value in expected.items()), "expected": expected, "actual": row}
    identities = {}
    for iid, (name, activity) in IDENTITY_PAIR_EXPECTED.items():
        row = connection.execute("SELECT i.canonical_name,s.co_report_activity FROM ingredients i LEFT JOIN ae_summary s ON s.ingredient_id=i.ingredient_id WHERE i.ingredient_id=?", (iid,)).fetchone()
        identities[iid] = {"passed": row is not None and row[0].casefold() == name and row[1] == activity, "actual": row, "expected_pair_activity": activity, "expected_name": name}
    related = connection.execute("""SELECT i.ingredient_id,i.canonical_name,s.report_count,s.co_report_activity FROM ingredients i LEFT JOIN ae_summary s ON s.ingredient_id=i.ingredient_id WHERE lower(i.canonical_name) IN ('atorvastatin','atorvastatin calcium','atorvastatin calcium anhydrous','atorvastatin calcium trihydrate','atorvastatin calcium propylene glycol solvate','metformin','metformin hydrochloride') ORDER BY i.ingredient_id""").fetchall()
    base = connection.execute("SELECT count(*) FROM ingredients i JOIN ae_summary s ON s.ingredient_id=i.ingredient_id WHERE lower(i.canonical_name)='atorvastatin'").fetchone()[0]
    return {"passed": all(check["passed"] for check in spots.values()) and all(check["passed"] for check in identities.values()) and base == 0,
        "report_level_spots": spots, "exact_salt_form_identities": identities, "related_distinct_identities": related, "base_atorvastatin_summary_rows": base}


def validate_ae(connection, report, derivation, expected_parent=None, check_benchmarks=True):
    result = validate_structure(connection); errors = result["errors"]
    result["scope"] = "PHASE4A_INGREDIENT_AE_ANALYTICS_ONLY; communications and publication not validated"
    projections = {}
    for table in PROJECTION_TABLES:
        where = " WHERE domain='ae_analytics'" if table == "coverage" else ""
        actual = {"projected_rows": connection.execute(f"SELECT count(*) FROM {table}" + where).fetchone()[0],
            "sha256_sorted_row_hashes": digest_rows(list(row) for row in connection.execute(f"SELECT * FROM {table}" + where))}
        expected = report["projection"][table]
        projections[table] = actual | {"passed": all(actual[field] == expected[field] for field in actual)}
        if not projections[table]["passed"]: errors.append({"gate": "exact_source_projection", "table": table})
    result["projected_row_checks"] = projections
    if expected_parent is not None:
        fingerprints = parent_fingerprints(connection)
        result["parent_preservation"] = {table: fingerprints[table] | {"parent": expected_parent[table], "passed": fingerprints[table] == expected_parent[table]} for table in expected_parent}
        for table, check in result["parent_preservation"].items():
            if not check["passed"]: errors.append({"gate": "frozen_parent_changed", "table": table})
    for table in UNSTARTED:
        if result["table_counts"][table]: errors.append({"gate": "unstarted_communication_table", "table": table})
    queries = {
        "summary_monthly_outcome_reconciliation": "SELECT count(*) FROM ae_summary s WHERE " + " OR ".join(f"s.{field}!=(SELECT sum(m.{field}) FROM ae_monthly m WHERE m.ingredient_id=s.ingredient_id)" for field in ("report_count", *FLAGS)),
        "summary_month_count_reconciliation": "SELECT count(*) FROM ae_summary s WHERE s.active_month_count!=(SELECT count(*) FROM ae_monthly m WHERE m.ingredient_id=s.ingredient_id)",
        "monthly_without_summary": "SELECT count(*) FROM ae_monthly m WHERE NOT EXISTS(SELECT 1 FROM ae_summary s WHERE s.ingredient_id=m.ingredient_id)",
        "reaction_without_summary": "SELECT count(*) FROM ae_top_reactions r WHERE NOT EXISTS(SELECT 1 FROM ae_summary s WHERE s.ingredient_id=r.ingredient_id)",
        "rank_gap_or_wrong_cap": "SELECT count(*) FROM (SELECT ingredient_id,count(*) n,max(rank) hi,min(rank) lo FROM ae_top_reactions GROUP BY ingredient_id) WHERE hi!=n OR lo!=1 OR n>50",
        "rank_wrong_order": """SELECT count(*) FROM ae_top_reactions a JOIN ae_top_reactions b ON b.ingredient_id=a.ingredient_id AND b.rank=a.rank+1 WHERE a.co_report_activity<b.co_report_activity OR (a.co_report_activity=b.co_report_activity AND a.reaction>b.reaction)""",
        "missing_ingredient_coverage": "SELECT count(*) FROM ingredients i WHERE NOT EXISTS(SELECT 1 FROM coverage c WHERE c.entity_type='INGREDIENT' AND c.entity_id=i.ingredient_id AND c.domain='ae_analytics' AND c.window_key='2020-01-01/2026-06-30')",
        "missing_product_coverage": "SELECT count(*) FROM products p WHERE NOT EXISTS(SELECT 1 FROM coverage c WHERE c.entity_type='PRODUCT' AND c.entity_id=p.product_id AND c.domain='ae_analytics' AND c.window_key='2020-01-01/2026-06-30')",
        "uncovered_ingredient_claimed_ready": "SELECT count(*) FROM coverage c WHERE c.entity_type='INGREDIENT' AND c.domain='ae_analytics' AND (EXISTS(SELECT 1 FROM ae_summary s WHERE s.ingredient_id=c.entity_id))!=(c.state='READY')",
        "product_report_count_scope": "SELECT count(*) FROM coverage c WHERE c.entity_type='PRODUCT' AND c.domain='ae_analytics' AND c.scope!='COMPONENT_ANALYTICS_AVAILABILITY_ONLY; NOT_PRODUCT_REPORT_COUNTS'"}
    checks = {name: connection.execute(sql).fetchone()[0] for name, sql in queries.items()}
    result["semantic_checks"] = checks
    for name, value in checks.items():
        if value: errors.append({"gate": name, "violations": value})
    result["product_coverage"] = product_coverage(connection)
    result["summed_ingredient_association_diagnostics"] = dict(zip(("report_count", "serious_report_count", "death_report_count", "hospitalization_report_count"), connection.execute("SELECT sum(report_count),sum(serious_report_count),sum(death_report_count),sum(hospitalization_report_count) FROM ae_summary").fetchone()))
    result["diagnostic_semantics"] = "Sums across ingredient memberships; not globally unique FAERS report totals."
    benchmarks = []
    def compare(name, actual, expected):
        check = {"measurement": name, "actual": actual, "expected": expected, "passed": actual == expected}
        benchmarks.append(check)
        if not check["passed"]: errors.append({"gate": "hard_benchmark_mismatch", **check})
    if check_benchmarks:
        for name, expected in {"release_ingredients": 7733, "ae_active_ingredients": 3174, "overlap": 3174, "absent": 0}.items(): compare("identity." + name, derivation["identity"][name], expected)
        for table, expected in {"ae_summary": 3174, "ae_monthly": 121453, "ae_top_reactions": 122755, "labels": 83684, "label_sections": 502104, "product_labels": 107377, "recalls": 17974, "product_recalls": 3332}.items(): compare("table." + table, result["table_counts"][table], expected)
        compare("top_reaction_ingredients", connection.execute("SELECT count(DISTINCT ingredient_id) FROM ae_top_reactions").fetchone()[0], 3174)
        for name, expected in {"total": 95426, "any_covered": 86617, "uncovered": 8809, "single_total": 78224, "single_covered": 69570, "combination_total": 17202, "combination_covered": 17047, "combination_fully_covered": 16302, "combination_partially_covered": 745}.items(): compare("normal_products." + name, result["product_coverage"].get(name, 0), expected)
        for name, expected in {"report_count": 8228685, "serious_report_count": 5491401, "death_report_count": 827164, "hospitalization_report_count": 2236383}.items(): compare("diagnostic." + name, result["summed_ingredient_association_diagnostics"][name], expected)
        for name, expected in {"reaction_aggregate_ingredient_month_rows": 121451, "report_derived_ingredient_month_rows": 121453, "report_only_rows": EXTRA_MONTHS, "reaction_aggregate_only_rows": []}.items():
            actual = derivation["monthly_reconciliation"][name]
            if name.endswith("rows") and isinstance(actual, list): actual = [list(row) for row in actual]
            compare("monthly_reconciliation." + name, actual, expected)
        result["spot_checks"] = spot_checks(connection)
        if not result["spot_checks"]["passed"]: errors.append({"gate": "spot_checks"})
    result["benchmarks"] = benchmarks; result["passed"] = not errors
    return result
