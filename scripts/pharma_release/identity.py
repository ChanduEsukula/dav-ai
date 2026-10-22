"""Source-exact identity ingestion. No inferred kit membership or equivalence."""
from collections import Counter, defaultdict
import hashlib
import json

from . import POLICY_VERSION
from .eligibility import decide, normalize_name, HUMAN_TYPES, LISTING_SEMANTICS
from .ids import existing_id, qualified_id, require_identifier
from .sources import canonical_json, SourceError

IDENTITY_TABLES = ("ingredients", "formulations", "products", "product_ingredients", "product_identifiers", "search_names")


def parquet_rows(path):
    import pyarrow.parquet as pq
    for batch in pq.ParquetFile(path).iter_batches(batch_size=1000):
        yield from batch.to_pylist()


def digest_rows(rows):
    hashes = sorted(hashlib.sha256(canonical_json(row).encode()).digest() for row in rows)
    return hashlib.sha256(b"".join(hashes)).hexdigest()


class Recorder:
    """Validate every SQLite-projected field against independent expected rows."""
    def __init__(self, connection):
        self.connection = connection
        self.columns = {t: [r[1] for r in connection.execute(f"PRAGMA table_info({t})")]
                        for t in (*IDENTITY_TABLES, "coverage")}
        self.hashes = defaultdict(list)
        self.counts = Counter()

    def insert(self, table, row):
        columns = self.columns[table]
        values = [row.get(c) for c in columns]
        self.connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
        self.hashes[table].append(hashlib.sha256(canonical_json(values).encode()).digest())
        self.counts[table] += 1

    def expected_digests(self):
        return {t: {"rows": self.counts[t], "sha256_sorted_row_hashes": hashlib.sha256(b"".join(sorted(self.hashes[t]))).hexdigest()}
                for t in self.columns}


def distinct_identifiers(values):
    if not isinstance(values, list):
        raise SourceError("Identifier arrays must remain arrays")
    return sorted({require_identifier(v) for v in values})


def source_text(value):
    if value is not None and not isinstance(value, str):
        raise SourceError("Expected nullable source text")
    return value


def add_search(recorder, entity, identifier, role, original, source):
    normalized = normalize_name(original)
    if not normalized:
        return
    recorder.insert("search_names", {"entity_type": entity, "entity_id": identifier,
        "ingredient_id": identifier if entity == "INGREDIENT" else None,
        "product_id": identifier if entity == "PRODUCT" else None, "name_role": role,
        "normalized_name": normalized, "original_names_json": canonical_json([original]), "source_id": source})


def add_coverage(recorder, entity, identifier, state, reason, count, unresolved, limitations):
    recorder.insert("coverage", {"entity_type": entity, "entity_id": identifier,
        {"INGREDIENT": "ingredient_id", "PRODUCT": "product_id", "FORMULATION": "formulation_id"}[entity]: identifier,
        "domain": "identity", "window_key": "", "state": state, "reason_code": reason,
        "scope": entity, "as_of_date": "2026-09-26", "source_date": "2026-09-26",
        "measured_count": count, "unresolved_count": unresolved, "rule_version": POLICY_VERSION,
        "limitations_json": canonical_json(limitations)})


def verify_product_projection(product, envelope, raw, ingredients, formulations):
    sid = require_identifier(product["source_id"])
    if sid != envelope["source_id"] or sid != raw.get("product_id"):
        raise SourceError("Raw/projection source identity mismatch")
    for field in ("generic_name", "brand_name", "labeler_name"):
        if product.get(field) != raw.get(field):
            raise SourceError("Source name projection mismatch: " + sid + ":" + field)
    if product["source_url"] != envelope["source_url"] or product["observed_at"] != envelope["observed_at"] or envelope["export_date"] != "2026-09-26":
        raise SourceError("Product provenance mismatch: " + sid)
    active = raw.get("active_ingredients") or []
    if not isinstance(active, list):
        raise SourceError("Active ingredient source shape mismatch")
    complete = bool(active) and all(isinstance(v, dict) and normalize_name(v.get("name")) for v in active)
    members = product["ingredient_ids"]
    if len(members) != len(set(members)) or any(v not in ingredients for v in members):
        raise SourceError("Duplicate/missing ingredient identity: " + sid)
    names = sorted({normalize_name(v["name"]) for v in active}) if complete else []
    actual_names = sorted(ingredients[v]["canonical_name"] for v in members)
    if names != actual_names or bool(members) != complete:
        raise SourceError("Full ingredient set differs from raw source: " + sid)
    raw_ids = {"product_ndcs": [raw["product_ndc"]] if raw.get("product_ndc") else [],
        "package_ndcs": [p["package_ndc"] for p in raw.get("packaging", []) if p.get("package_ndc")],
        "rxcuis": (raw.get("openfda") or {}).get("rxcui") or []}
    for field, values in raw_ids.items():
        if distinct_identifiers(product[field]) != distinct_identifiers(values):
            raise SourceError("Identifier projection mismatch: " + sid + ":" + field)
    fid = product["formulation_id"]
    if fid is not None:
        formulation = formulations.get(fid)
        if formulation is None or set(formulation["ingredient_ids"]) != set(members):
            raise SourceError("Formulation membership mismatch: " + sid)
        strengths = sorted([normalize_name(v.get("name")), normalize_name(v.get("strength"))] for v in active)
        routes = sorted({normalize_name(v) for v in raw.get("route") or [] if normalize_name(v)})
        if (json.loads(formulation["strengths_json"]) != strengths or formulation["dosage_form"] != normalize_name(raw.get("dosage_form"))
                or formulation["routes"] != routes):
            raise SourceError("Formulation source fields mismatch: " + sid)


def populate_identity(connection, ingredient_rows, formulation_rows, product_rows, raw_rows, raw_source, identity_source, audit_stream):
    recorder = Recorder(connection)
    ingredients = {}; formulations = {}; products = {}
    for row in ingredient_rows:
        iid = existing_id(row["ingredient_id"], "ingredient")
        if iid in ingredients or row["source"] != "openfda_ndc_directory":
            raise SourceError("Duplicate/unexpected ingredient source")
        ingredients[iid] = row
        recorder.insert("ingredients", {k: row[k] for k in ("ingredient_id", "canonical_name", "identity_rule", "observed_at")} | {"source_id": identity_source})
        add_search(recorder, "INGREDIENT", iid, "INGREDIENT", row["canonical_name"], identity_source)
        add_coverage(recorder, "INGREDIENT", iid, "READY", "EXACT_NORMALIZED_SOURCE_NAME", 1, 0,
                     ["Exact case/whitespace-normalized source name; salts not merged; no chemical equivalence claim."])
    for row in formulation_rows:
        fid = existing_id(row["formulation_id"], "formulation")
        if fid in formulations or any(v not in ingredients for v in row["ingredient_ids"]):
            raise SourceError("Duplicate/unresolved formulation identity")
        formulations[fid] = row
        recorder.insert("formulations", {"formulation_id": fid, "ingredient_ids_json": canonical_json(row["ingredient_ids"]),
            "strengths_json": row["strengths_json"], "dosage_form": row["dosage_form"], "routes_json": canonical_json(row["routes"]), "source_id": identity_source})
        add_coverage(recorder, "FORMULATION", fid, "READY", "PRESERVED_SOURCE_FORMULATION", len(row["ingredient_ids"]), 0,
                     ["Complete source ingredient/strength/form/route identity; not a clinical equivalence assertion."])
    for row in product_rows:
        sid = require_identifier(row["source_id"])
        if sid in products:
            raise SourceError("Duplicate normalized source product")
        products[sid] = row
    modes = Counter(); reasons = Counter(); combos = Counter(); presentations = Counter(); types = Counter(); categories = Counter()
    finished = Counter(); listing = Counter(); identifier_counts = defaultdict(Counter); alias_counts = defaultdict(Counter)
    alias_sets = defaultdict(set); unknown_aliases = set(); seen = set(); partial = 0; excluded_ids = []
    for envelope in raw_rows:
        sid = require_identifier(envelope["source_id"])
        if sid in seen or sid not in products:
            raise SourceError("Duplicate/unjoined raw source product")
        seen.add(sid)
        product = products[sid]; raw = json.loads(envelope["raw_json"])
        verify_product_projection(product, envelope, raw, ingredients, formulations)
        decision = decide(product, raw)
        mode = decision["eligibility_mode"]; members = product["ingredient_ids"]
        modes[mode] += 1; reasons[decision["eligibility_reason"]] += 1
        combos[mode] += int(len(members) > 1); partial += decision["identity_partial"]
        presentations[decision["consumer_classification"]] += 1
        types[raw.get("product_type")] += 1; listing[decision["listing_date_status"]] += 1
        if raw.get("finished") is True and raw.get("product_type") in HUMAN_TYPES:
            finished["total"] += 1
            categories[raw.get("marketing_category")] += 1
            finished["resolved" if members else "unresolved"] += 1
            if members:
                finished["combination" if len(members) > 1 else "single"] += 1
            else:
                finished["unresolved_KIT" if raw.get("dosage_form") == "KIT" else "unresolved_non_KIT"] += 1
            finished["with_formulation"] += int(product["formulation_id"] is not None)
            finished["with_rxcui"] += int(bool(product["rxcuis"]))
        for kind, field in (("PRODUCT_NDC", "product_ndcs"), ("PACKAGE_NDC", "package_ndcs"), ("RXCUI", "rxcuis")):
            for value in distinct_identifiers(product[field]):
                identifier_counts[kind][value] += 1
        source_names = {"GENERIC": raw.get("generic_name"), "BRAND": raw.get("brand_name"), "BRAND_BASE": raw.get("brand_name_base")}
        for role, original in source_names.items():
            name = normalize_name(original)
            if name:
                alias_counts[role][name] += 1
                if members:
                    alias_sets[name].add(tuple(sorted(members)))
                else:
                    unknown_aliases.add(name)
        included = mode != "EXCLUDED_V1"
        pid = qualified_id("product", "openfda_ndc_directory", sid)
        audit = {"source_record_id": sid, "product_id": pid, "retained_in_sqlite": included,
                 **decision, "source_fields": {field: raw.get(field) for field in
                    ("generic_name", "brand_name", "brand_name_base", "labeler_name", "product_type", "marketing_category", "marketing_start_date", "marketing_end_date", "listing_expiration_date", "application_number", "dosage_form", "route", "finished")},
                 "ingredient_ids": members, "formulation_id": product["formulation_id"],
                 "identifiers": {k: product[k] for k in ("product_ndcs", "package_ndcs", "rxcuis")}}
        audit_stream.write(canonical_json(audit) + "\n")
        if not included:
            excluded_ids.append(sid)
            continue
        row = {"product_id": pid, "source_id": raw_source, "source_record_id": sid,
            "source_url": envelope["source_url"], "observed_at": envelope["observed_at"],
            **{k: source_text(raw.get(k)) for k in ("generic_name", "brand_name", "brand_name_base", "labeler_name", "product_type", "marketing_category", "application_number", "dosage_form")},
            **{k + "_raw": source_text(raw.get(k)) for k in ("marketing_start_date", "marketing_end_date", "listing_expiration_date")},
            "formulation_id": product["formulation_id"], "active_ingredients_json": canonical_json(raw["active_ingredients"]) if "active_ingredients" in raw else None,
            "ingredient_set_complete": int(bool(members)), "is_combination": int(len(members) > 1),
            "eligibility_mode": mode, "eligibility_reason": decision["eligibility_reason"],
            "additional_deficiencies_json": canonical_json(decision["additional_deficiencies"]),
            "identity_partial": decision["identity_partial"], "policy_version": POLICY_VERSION,
            "finished": int(raw["finished"]) if type(raw.get("finished")) is bool else None,
            "routes_json": canonical_json(raw["route"]) if raw.get("route") is not None else None,
            "consumer_classification": decision["consumer_classification"]}
        recorder.insert("products", row)
        for iid in members:
            recorder.insert("product_ingredients", {"product_id": pid, "ingredient_id": iid})
        for kind, field in (("PRODUCT_NDC", "product_ndcs"), ("PACKAGE_NDC", "package_ndcs"), ("RXCUI", "rxcuis")):
            for value in distinct_identifiers(product[field]):
                recorder.insert("product_identifiers", {"product_id": pid, "identifier_type": kind, "value": value,
                    "source_id": raw_source, "rxcui_concept_type": "UNKNOWN" if kind == "RXCUI" else None,
                    "is_unique_product": 0, "has_conflict": 0})
        for role, original in source_names.items():
            add_search(recorder, "PRODUCT", pid, role, original, raw_source)
        state = "UNKNOWN" if not members else ("PARTIAL" if not product["formulation_id"] or decision["identity_partial"] else "READY")
        reason = "UNRESOLVED_INGREDIENT_AND_FORMULATION" if not members else ("SOURCE_IDENTITY_GAPS" if state == "PARTIAL" else "SOURCE_IDENTITY_PRESERVED")
        add_coverage(recorder, "PRODUCT", pid, state, reason, len(members) if members else None, 1 if state != "READY" else 0,
            [LISTING_SEMANTICS, "Source brand_name is a display alias, not an exclusive commercial-brand assertion.",
             "Marketing category is preserved; directory listing does not independently establish approval.",
             *(["No ingredient or formulation inferred from kit names."] if not members else [])])
    if seen != set(products):
        raise SourceError("Normalized products absent from raw source")
    # Identifier flags use the entire source universe, including offline exclusions.
    for kind, counts in identifier_counts.items():
        connection.executemany("UPDATE product_identifiers SET is_unique_product=?,has_conflict=? WHERE identifier_type=? AND value=?",
            [(int(n == 1), int(n > 1), kind, value) for value, n in sorted(counts.items())])
    # Adjust expected flag hashes independently from the same measured source multiplicity.
    recorder.hashes["product_identifiers"] = []
    cols = recorder.columns["product_identifiers"]
    for sid in sorted(seen - set(excluded_ids)):
        product = products[sid]; pid = qualified_id("product", "openfda_ndc_directory", sid)
        for kind, field in (("PRODUCT_NDC", "product_ndcs"), ("PACKAGE_NDC", "package_ndcs"), ("RXCUI", "rxcuis")):
            for value in distinct_identifiers(product[field]):
                n = identifier_counts[kind][value]
                row = {"product_id": pid, "identifier_type": kind, "value": value, "source_id": raw_source,
                    "rxcui_concept_type": "UNKNOWN" if kind == "RXCUI" else None, "is_unique_product": int(n == 1), "has_conflict": int(n > 1)}
                recorder.hashes["product_identifiers"].append(hashlib.sha256(canonical_json([row.get(c) for c in cols]).encode()).digest())
    return {"source_product_count": len(seen), "retained_product_count": len(seen) - len(excluded_ids),
        "eligibility_counts": dict(modes), "primary_reason_counts": dict(reasons), "combination_counts": dict(combos),
        "normal_consumer_identity_partial": partial, "source_presentation_counts": dict(presentations),
        "source_product_types": dict(types), "finished_human": dict(finished), "finished_human_marketing_categories": dict(categories),
        "source_listing_date_status": dict(listing), "source_identifier_counts": {k: {"distinct_values": len(v),
            "products_with_identifier": sum(bool(p[field]) for p in products.values()),
            "association_rows": sum(v.values()), "ambiguous_values": sum(n > 1 for n in v.values()),
            "max_candidates": max(v.values(), default=0)} for k, field in (("PRODUCT_NDC", "product_ndcs"), ("PACKAGE_NDC", "package_ndcs"), ("RXCUI", "rxcuis")) for v in [identifier_counts[k]]},
        "source_name_ambiguity": {role: {"distinct_names": len(v), "ambiguous_names": sum(n > 1 for n in v.values()), "max_products": max(v.values(), default=0)} for role, v in alias_counts.items()},
        "source_search_names_multiple_resolved_ingredient_sets": sum(len(v) > 1 for v in alias_sets.values()),
        "source_search_names_with_unresolved_identity": len(unknown_aliases),
        "excluded_source_record_ids": excluded_ids, "expected_sqlite_rows": recorder.expected_digests()}
