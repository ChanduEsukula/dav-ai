"""Explicit text NDC only; exact frozen identity, independent edge precedence."""
from collections import defaultdict
import json
import re

from . import POLICY_VERSION
from .sources import canonical_json, SourceError

RULE_VERSION = "phase3b-explicit-text-ndc-package-precedence-v1"
TEXT_FIELDS = ("product_description", "code_info", "more_code_info")
NDC_PATTERN = r"(?i)\bNDC\s*[:#-]?\s*(\d{4,6})\s*-\s*(\d{3,4})(?:\s*-\s*(\d{1,3}))?"
NDC = re.compile(NDC_PATTERN)


def extract_text_ndcs(raw):
    occurrences = []
    for field in TEXT_FIELDS:
        text = raw.get(field)
        if text is None:
            continue
        if type(text) is not str:
            raise SourceError("Unexpected recall text field type: " + field)
        for match in NDC.finditer(text):
            segments = [v for v in match.groups() if v is not None]
            occurrences.append({"field": field, "start": match.start(), "end": match.end(), "excerpt": match.group(),
                "text_ndc": "-".join(segments), "product_ndc": "-".join(segments[:2]), "package_style": len(segments) == 3,
                "parser_match_followed_by_digit": match.end() < len(text) and text[match.end()].isdigit()})
    return occurrences


class RecallIndex:
    def __init__(self, connection):
        self.identifiers = defaultdict(list)
        for kind, value, pid, unique, conflict in connection.execute("SELECT identifier_type,value,product_id,is_unique_product,has_conflict FROM product_identifiers WHERE identifier_type IN ('PACKAGE_NDC','PRODUCT_NDC')"):
            self.identifiers[kind, value].append((pid, unique, conflict))
        members = defaultdict(set)
        for pid, iid in connection.execute("SELECT product_id,ingredient_id FROM product_ingredients"):
            members[pid].add(iid)
        formulations = {fid: set(json.loads(ids)) for fid, ids in connection.execute("SELECT formulation_id,ingredient_ids_json FROM formulations")}
        self.products = {}
        for pid, fid, complete, mode, cls in connection.execute("SELECT product_id,formulation_id,ingredient_set_complete,eligibility_mode,consumer_classification FROM products"):
            ingredients_ok = bool(complete and members[pid])
            formulation_ok = bool(ingredients_ok and fid and formulations.get(fid) == members[pid])
            self.products[pid] = {"formulation_id": fid, "ingredient_ids": sorted(members[pid]),
                "ingredient_set_verified": int(ingredients_ok), "formulation_scope_verified": int(formulation_ok),
                "eligibility_mode": mode, "consumer_classification": cls}

    def resolve(self, occurrence):
        package = self.identifiers.get(("PACKAGE_NDC", occurrence["text_ndc"]), []) if occurrence["package_style"] else []
        product = self.identifiers.get(("PRODUCT_NDC", occurrence["product_ndc"]), [])
        # An ambiguous/conflicted package is held back, never converted into a
        # weaker apparent product match. Absent packages may use the product key.
        rows = package or product
        method = "EXACT_PACKAGE_NDC" if package else "EXACT_PRODUCT_NDC"
        value = occurrence["text_ndc"] if package else occurrence["product_ndc"]
        fragment = occurrence.get("parser_match_followed_by_digit", False)
        clean = not fragment and len(rows) == 1 and rows[0][1:] == (1, 0)
        return occurrence | {"resolution": "UNMATCHED" if fragment else "CLEAN" if clean else "AMBIGUOUS_OR_CONFLICTED" if rows else "UNMATCHED",
            "failure_reason": "MALFORMED_NDC_TOKEN_FRAGMENT_NOT_REPAIRED" if fragment else None,
            "product_id": rows[0][0] if clean else None, "candidate_product_ids": sorted({r[0] for r in rows}),
            "attempted_method": method, "matched_release_identifier": value if clean else None,
            "identity_rows": [{"product_id": pid, "is_unique_product": unique, "has_conflict": conflict} for pid, unique, conflict in sorted(rows)]}

    def admit(self, raw):
        occurrences = [self.resolve(o) for o in extract_text_ndcs(raw)]
        grouped = defaultdict(list)
        for occurrence in occurrences:
            if occurrence["resolution"] == "CLEAN":
                grouped[occurrence["product_id"]].append(occurrence)
        states = {o["resolution"] for o in occurrences}
        category = ("NO_EXPLICIT_TEXT_NDC" if not occurrences else "HAS_AMBIGUOUS_TEXT_NDC" if "AMBIGUOUS_OR_CONFLICTED" in states
            else "ALL_TEXT_NDCS_CLEAN" if states == {"CLEAN"} else "MIXED_CLEAN_AND_UNMATCHED" if "CLEAN" in states else "ALL_TEXT_NDCS_UNMATCHED")
        return {"category": category, "partial": bool(grouped and states != {"CLEAN"}), "occurrences": occurrences,
            "matches_by_product": dict(grouped), "unresolved": [o for o in occurrences if o["resolution"] != "CLEAN"]}

    def edge(self, pid, recall_id, raw, admission):
        matches = admission["matches_by_product"][pid]
        method = "EXACT_PACKAGE_NDC" if any(o["attempted_method"] == "EXACT_PACKAGE_NDC" for o in matches) else "EXACT_PRODUCT_NDC"
        best = min((o for o in matches if o["attempted_method"] == method), key=lambda o: (o["matched_release_identifier"], o["field"], o["start"]))
        product = self.products[pid]
        basis = {"rule_version": RULE_VERSION, "applicability_method": method, "authority": "EXPLICIT_RECALL_TEXT_NDC",
            "matching_occurrences": matches, "selected_text_ndc": best["text_ndc"], "matched_release_identifier": best["matched_release_identifier"],
            "recall_applicability_partial": admission["partial"], "recall_unresolved_identifiers": admission["unresolved"],
            "frozen_product_identity": product,
            "ingredient_formulation_basis": "Exact clean text NDC identifies this frozen product, its full ingredient membership and formulation. Membership is checked against the frozen formulation; no independent composition/strength/name inference from recall text or harmonized metadata.",
            "lots": {"code_info": raw.get("code_info"), "more_code_info": raw.get("more_code_info"),
                "interpretation": "Verbatim source restrictions retained; not parsed into package-level/all-lots claims."},
            "openfda_role": "SUPPORTING_METADATA_ONLY_NOT_SCOPE_AUTHORITY"}
        return {"product_id": pid, "recall_id": recall_id,
            "applicability_class": "AFFECTED_PACKAGE" if method == "EXACT_PACKAGE_NDC" else "AFFECTED_PRODUCT",
            "match_method": method, "matched_value": best["matched_release_identifier"], "explicit_scope_verified": 1,
            "ingredient_set_verified": product["ingredient_set_verified"], "formulation_scope_verified": product["formulation_scope_verified"],
            "lot_scope": "UNKNOWN", "lot_code_text": raw.get("code_info"), "verification_basis_json": canonical_json(basis),
            "conflicts_json": "[]", "consumer_eligible": int(product["consumer_classification"] == "NORMAL_CONSUMER_HUMAN_PRODUCT"
                and product["eligibility_mode"] == "NORMAL_CONSUMER" and product["ingredient_set_verified"] and product["formulation_scope_verified"]), "policy_version": POLICY_VERSION}
