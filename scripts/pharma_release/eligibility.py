"""Ordered contract-v1 decisions against the pinned directory observation date."""
from datetime import datetime, date
import re

OBSERVATION_DATE = date(2026, 9, 26)
HUMAN_TYPES = {"HUMAN PRESCRIPTION DRUG", "HUMAN OTC DRUG"}
ALLOWED_TYPES = HUMAN_TYPES | {"VACCINE", "PLASMA DERIVATIVE"}
ALLOWED_CATEGORIES = {"ANDA", "NDA", "NDA AUTHORIZED GENERIC", "BLA", "OTC MONOGRAPH DRUG", "OTC MONOGRAPH FINAL"}
EXCLUDED_TYPES = {"BULK INGREDIENT", "DRUG FOR FURTHER PROCESSING", "ANIMAL DRUG FOR FURTHER PROCESSING", "LICENSED VACCINE BULK INTERMEDIATE"}
LISTING_SEMANTICS = "Listing dates were active as of the 2026-09-26 directory snapshot; not a claim of current sale, availability or independent FDA approval."


def normalize_name(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Source name must be a string or NULL")
    return " ".join(value.casefold().split())


def parse_source_date(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{8}", value):
        raise ValueError("Supplied listing date is not exact YYYYMMDD")
    return datetime.strptime(value, "%Y%m%d").date()


def listing_deficiencies(raw):
    reasons = []
    for field, reason in (("marketing_start_date", "MARKETING_NOT_STARTED"),
                          ("marketing_end_date", "MARKETING_ENDED"),
                          ("listing_expiration_date", "LISTING_EXPIRED")):
        try:
            value = parse_source_date(raw.get(field))
        except ValueError:
            reasons.append("MALFORMED_" + field.upper())
            continue
        if value is None:
            continue
        if ((field == "marketing_start_date" and value > OBSERVATION_DATE)
                or (field == "marketing_end_date" and value <= OBSERVATION_DATE)
                or (field == "listing_expiration_date" and value < OBSERVATION_DATE)):
            reasons.append(reason)
    return reasons


def decide(product, raw):
    deficiencies = []
    kind = raw.get("product_type")
    if kind in EXCLUDED_TYPES:
        deficiencies.append("NON_FINISHED_PRODUCT")
    elif kind not in ALLOWED_TYPES:
        deficiencies.append("SPECIAL_PRODUCT_TYPE")
    if raw.get("marketing_category") not in ALLOWED_CATEGORIES:
        deficiencies.append("MARKETING_CATEGORY_NOT_ALLOWED")
    if not product["ingredient_ids"]:
        deficiencies.append("UNRESOLVED_INGREDIENT_SET")
    if not (normalize_name(raw.get("generic_name")) or normalize_name(raw.get("brand_name"))) or not product["product_ndcs"]:
        deficiencies.append("MISSING_DISPLAY_OR_PRODUCT_NDC")
    deficiencies.extend(listing_deficiencies(raw))
    reason = deficiencies[0] if deficiencies else "ELIGIBLE"
    mode = "EXCLUDED_V1" if kind in EXCLUDED_TYPES else ("REGULATORY_ONLY" if deficiencies else "NORMAL_CONSUMER")
    if not product.get("formulation_id"):
        deficiencies.append("FORMULATION_UNRESOLVED")
    for field in ("marketing_start_date", "listing_expiration_date"):
        if not raw.get(field):
            deficiencies.append("MISSING_" + field.upper())
    partial = mode == "NORMAL_CONSUMER" and any(v in deficiencies for v in
        ("FORMULATION_UNRESOLVED", "MISSING_MARKETING_START_DATE", "MISSING_LISTING_EXPIRATION_DATE"))
    if mode == "NORMAL_CONSUMER":
        presentation = "NORMAL_CONSUMER_HUMAN_PRODUCT"
    elif kind in ALLOWED_TYPES and not product["ingredient_ids"]:
        presentation = "UNRESOLVED_IDENTITY"
    elif kind in ALLOWED_TYPES:
        presentation = "SPECIAL_REGULATORY_CATEGORY_HUMAN_PRODUCT"
    else:
        presentation = "REGULATORY_RESEARCH_ONLY"
    dates = listing_deficiencies(raw)
    return {"eligibility_mode": mode, "eligibility_reason": reason,
            "additional_deficiencies": [v for v in deficiencies if v != reason],
            "identity_partial": int(partial), "consumer_classification": presentation,
            "listing_date_status": dates[0] if dates else "ACTIVE_BY_DATES"}
