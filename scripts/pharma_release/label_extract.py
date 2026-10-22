"""Lossless structured label sections and source-bounded date/version metadata."""
from datetime import date, datetime
import hashlib
import re

from .ids import qualified_id, require_identifier
from .sources import canonical_json, SourceError

FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings", "contraindications", "adverse_reactions", "drug_interactions")
OPTIONAL_FIELD = "warnings_and_precautions"
EXPORT_DATE = date(2026, 9, 25)
SOURCE_NAME = "openfda_drug_label"


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_effective(value):
    parsed = None
    if isinstance(value, str) and re.fullmatch(r"[0-9]{8}", value):
        try:
            parsed = datetime.strptime(value, "%Y%m%d").date()
        except ValueError:
            pass
    return (parsed.isoformat(), "VALID" if parsed <= EXPORT_DATE else "FUTURE_AT_SOURCE_EXPORT") if parsed else (None, "INVALID")


def parse_version(value):
    if type(value) is int and value >= 0:
        version = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        version = int(value)
    else:
        return None
    if version > 2**63 - 1:
        # The original value remains lossless in version_raw_json. Never clamp,
        # wrap or stringify a fabricated parsed version for consumer selection.
        return None
    return version


def source_integer_version(value):
    return (type(value) is int and value >= 0) or (isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None)


def section_slot(raw, field, label_id):
    present = field in raw
    value = raw.get(field)
    original = canonical_json(value) if present else None
    valid = False; text = None
    if not present:
        shape = "ABSENT"; reason = "SOURCE_FIELD_NOT_PRESENT"
    elif isinstance(value, str):
        shape = "STRING"; text = value; valid = True; reason = "SOURCE_FIELD_EMPTY"
    elif isinstance(value, list) and all(isinstance(v, str) for v in value):
        shape = "ARRAY_OF_STRINGS"; text = "\n\n".join(value); valid = True; reason = "SOURCE_FIELD_EMPTY"
    else:
        shape = "INVALID_" + type(value).__name__.upper(); reason = "EXTRACTION_FAILED"
    nonblank = valid and bool(text.strip())
    if nonblank:
        reason = "EXACT_SOURCE_TEXT_PRESERVED"
    return {"label_id": label_id, "source_field": field, "normalized_section": field,
        "field_present": int(present), "original_value_json": original, "full_text": text,
        "source_shape": shape, "state": "READY" if nonblank else "UNAVAILABLE", "reason_code": reason,
        "source_value_sha256": sha(original) if original is not None else None,
        "rendering_sha256": sha(text) if text is not None else None}


def project_label(raw, source_id):
    identifier = qualified_id("label", SOURCE_NAME, require_identifier(raw.get("id")))
    set_id = require_identifier(raw.get("set_id"))
    of = raw.get("openfda")
    if of is None:
        of = {}
    if not isinstance(of, dict):
        raise SourceError("Unexpected openfda source object shape")
    fields = FIELDS + ((OPTIONAL_FIELD,) if OPTIONAL_FIELD in raw else ())
    sections = [section_slot(raw, field, identifier) for field in fields]
    effective, status = parse_effective(raw.get("effective_time"))
    if raw.get("effective_time") is not None and not isinstance(raw["effective_time"], str):
        raise SourceError("Cannot losslessly project nonstring effective_time")
    label = {"label_id": identifier, "source_id": source_id, "source_record_id": raw["id"], "set_id": set_id,
        "version_raw_json": canonical_json(raw.get("version")), "version_number": parse_version(raw.get("version")),
        "effective_time_raw": raw.get("effective_time"), "effective_date": effective, "date_status": status,
        "source_identity_json": canonical_json(of), "has_requested_safety_section": int(any(s["state"] == "READY" for s in sections if s["source_field"] in FIELDS)),
        "extraction_valid": int(all(s["reason_code"] != "EXTRACTION_FAILED" for s in sections)),
        "source_content_sha256": sha(canonical_json(raw))}
    return label, sections
