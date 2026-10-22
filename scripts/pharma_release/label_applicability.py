"""All-NDC admission, independent corroboration, and per-product/set selection."""
from collections import defaultdict
import json

from . import POLICY_VERSION
from .eligibility import normalize_name
from .sources import canonical_json, SourceError

RULE_VERSION = "phase3a-all-product-ndcs-unique-conflict-free-v1"


class ProductIndex:
    def __init__(self, connection):
        self.ndcs = defaultdict(list)
        for value, pid, unique, conflict in connection.execute("SELECT value,product_id,is_unique_product,has_conflict FROM product_identifiers WHERE identifier_type='PRODUCT_NDC'"):
            self.ndcs[value].append((pid, unique, conflict))
        names = dict(connection.execute("SELECT ingredient_id,canonical_name FROM ingredients"))
        self.products = {}
        for pid, fid, routes, kind, mode, combo in connection.execute("SELECT product_id,formulation_id,routes_json,product_type,eligibility_mode,is_combination FROM products"):
            self.products[pid] = {"formulation_id": fid, "routes": sorted({normalize_name(v) for v in json.loads(routes)}) if routes else [],
                "product_type": kind, "eligibility_mode": mode, "is_combination": combo, "ingredient_names": [], "rxcuis": set()}
        for pid, iid in connection.execute("SELECT product_id,ingredient_id FROM product_ingredients ORDER BY product_id,ingredient_id"):
            self.products[pid]["ingredient_names"].append(names[iid])
        for pid, value in connection.execute("SELECT product_id,value FROM product_identifiers WHERE identifier_type='RXCUI'"):
            self.products[pid]["rxcuis"].add(value)
        for product in self.products.values():
            product["ingredient_names"].sort()

    def admit(self, raw):
        of = raw.get("openfda") or {}
        values = of.get("product_ndc") or []
        if not isinstance(values, list) or any(type(v) is not str or not v.strip() for v in values):
            raise SourceError("Unexpected product_ndc identity array shape")
        values = sorted(set(values))  # original ordered array remains in labels.
        if not values:
            return {"admitted": False, "reason": "NO_PRODUCT_NDC", "matched": [], "unmatched": [], "conflicted": [], "candidates": [], "all_ndcs": []}
        missing = [v for v in values if not self.ndcs.get(v)]
        bad = [v for v in values if self.ndcs.get(v) and (len(self.ndcs[v]) != 1 or self.ndcs[v][0][1:] != (1, 0))]
        matched = [v for v in values if self.ndcs.get(v)]
        candidates = sorted({pid for value in matched for pid, _, _ in self.ndcs[value]})
        return {"admitted": not missing and not bad,
            "reason": "AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC" if bad else ("UNMATCHED_PRODUCT_NDC" if missing else "CLEAN_ALL_PRODUCT_NDCS"),
            "matched": matched, "unmatched": missing, "conflicted": bad, "candidates": candidates, "all_ndcs": values}


def normalized_array(of, field):
    values = of.get(field) or []
    if not isinstance(values, list) or any(type(v) is not str for v in values):
        raise SourceError("Unexpected harmonized identity array: " + field)
    return sorted({normalize_name(v) for v in values if normalize_name(v)})


def edge_projection(label, raw, admission, ndc, index):
    pid = index.ndcs[ndc][0][0]; product = index.products[pid]; of = raw.get("openfda") or {}
    substances = normalized_array(of, "substance_name"); routes = normalized_array(of, "route")
    conflicts = []; unresolved = []
    ingredient_ok = bool(product["ingredient_names"]) and bool(substances) and product["ingredient_names"] == substances
    if product["ingredient_names"] and substances and not ingredient_ok:
        conflicts.append("EXACT_INGREDIENT_SET_CONFLICT")
    elif not ingredient_ok:
        unresolved.append("INGREDIENT_SET_NOT_CORROBORATED")
    route_ok = bool(product["routes"]) and bool(routes) and set(product["routes"]).issubset(routes)
    if product["routes"] and routes and not route_ok:
        conflicts.append("EXACT_ROUTE_CONFLICT")
    elif not route_ok:
        unresolved.append("ROUTE_NOT_CORROBORATED")
    kinds = of.get("product_type") or []
    if kinds and product["product_type"] and product["product_type"] not in kinds:
        conflicts.append("SOURCE_PRODUCT_TYPE_CONFLICT")
    rxcuis = of.get("rxcui") or []
    if rxcuis and product["rxcuis"] and not product["rxcuis"].intersection(rxcuis):
        conflicts.append("SOURCE_RXCUI_CONFLICT")
    if not product["formulation_id"]:
        unresolved.append("PRODUCT_FORMULATION_UNRESOLVED")
    formulation_ok = ingredient_ok and route_ok and bool(product["formulation_id"]) and not conflicts
    basis = {"rule_version": RULE_VERSION, "source_field": "openfda.product_ndc", "matched_product_ndc": ndc,
        "all_label_product_ndcs": admission["all_ndcs"], "every_referenced_ndc_unique_and_conflict_free": True,
        "phase2_flags": {"is_unique_product": 1, "has_conflict": 0},
        "label_ingredient_names_exact_normalized": substances, "product_ingredient_names": product["ingredient_names"],
        "label_routes_exact_normalized": routes, "product_routes": product["routes"], "product_formulation_id": product["formulation_id"],
        "formulation_basis": "Explicit listed NDC identifies the preserved product formulation; full ingredient set and route are independently cross-checked. No free-text strength/form parsing or chemical equivalence is asserted.",
        "consumer_product_mode": product["eligibility_mode"]}
    return {"product_id": pid, "label_id": label["label_id"], "applicability_class": "AMBIGUOUS" if conflicts else "EXACT_PRODUCT",
        "match_method": "EXACT_NDC", "matched_value": ndc, "is_combination": product["is_combination"],
        "ingredient_set_verified": int(ingredient_ok), "formulation_scope_verified": int(formulation_ok),
        "evidence_scope": "UNKNOWN" if conflicts else "PRODUCT", "verification_basis_json": canonical_json(basis),
        "conflicts_json": canonical_json(conflicts), "unresolved_identifiers_json": canonical_json(unresolved),
        "selection_status": "NOT_SELECTED", "consumer_eligible": 0, "policy_version": POLICY_VERSION}


def select_group(records, blockers=()):
    """Records are one product and source set. Different label sets are independent."""
    output = {r["label_id"]: ("NOT_SELECTED", 0) for r in records}
    eligible = [r for r in records if r["viable"]]
    if not eligible:
        return output
    if any(r["version"] is None for r in (*records, *blockers)):
        return {k: ("AMBIGUOUS", 0) for k in output}
    dated = sorted((r["version"], r["date"]) for r in (*records, *blockers) if r["date"] is not None)
    if any(v1 < v2 and d1 > d2 for (v1, d1), (v2, d2) in zip(dated, dated[1:])):
        return {k: ("AMBIGUOUS", 0) for k in output}
    highest = max(r["version"] for r in eligible)
    top = [r for r in eligible if r["version"] == highest]
    if len({r["selection_fingerprint"] for r in top}) > 1:
        return {k: ("AMBIGUOUS", 0) for k in output}
    # A rejected/unusable preserved candidate at the same version makes selection uncertain.
    if any(r["version"] == highest for r in blockers) or any(r["version"] == highest and not r["viable"] for r in records):
        return {k: ("AMBIGUOUS", 0) for k in output}
    earlier = any(r["version"] > highest for r in (*records, *blockers))
    for r in top:
        output[r["label_id"]] = ("EARLIER_STORED" if earlier else "SELECTED_STORED", int(r["normal_consumer"]))
    return output
