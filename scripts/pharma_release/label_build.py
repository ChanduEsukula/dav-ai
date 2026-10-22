"""Streaming admitted label projection, replay guards, selection and coverage."""
from collections import Counter, defaultdict
import hashlib
import json

from . import POLICY_VERSION
from .label_applicability import edge_projection, select_group
from .label_extract import FIELDS, OPTIONAL_FIELD, parse_effective, parse_version, project_label, sha, source_integer_version
from .sources import canonical_json, SourceError

PROJECTION_TABLES = ("labels", "label_sections", "product_labels")
DYNAMIC_EDGE_FIELDS = {"selection_status", "consumer_eligible"}


def row_hash(values):
    return hashlib.sha256(canonical_json(values).encode()).digest()


class LabelWriter:
    def __init__(self, connection):
        self.connection = connection
        self.columns = {t: [r[1] for r in connection.execute(f"PRAGMA table_info({t})")] for t in PROJECTION_TABLES}
        self.keys = {t: [r[1] for r in sorted(connection.execute(f"PRAGMA table_info({t})"), key=lambda r: r[5]) if r[5]] for t in PROJECTION_TABLES}
        self.hashes = defaultdict(list); self.counts = Counter(); self.inserted = Counter(); self.replayed = Counter()

    def put(self, table, row):
        columns = self.columns[table]; keys = self.keys[table]
        cursor = self.connection.execute(f"SELECT {','.join(columns)} FROM {table} WHERE " + " AND ".join(k + "=?" for k in keys), [row[k] for k in keys])
        old = cursor.fetchone()
        values = [row.get(k) for k in columns]
        if old is None:
            self.connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
            self.inserted[table] += 1
        else:
            comparisons = [i for i, field in enumerate(columns) if table != "product_labels" or field not in DYNAMIC_EDGE_FIELDS]
            if any(old[i] != values[i] for i in comparisons):
                raise SourceError("Nonidentical replay/collision in " + table)
            self.replayed[table] += 1
        fingerprint = [row.get(k) for k in columns if table != "product_labels" or k not in DYNAMIC_EDGE_FIELDS]
        self.hashes[table].append(row_hash(fingerprint)); self.counts[table] += 1

    def report(self):
        return {t: {"projected_rows": self.counts[t], "inserted": self.inserted[t], "identical_replays": self.replayed[t],
                    "sha256_sorted_row_hashes": hashlib.sha256(b"".join(sorted(self.hashes[t]))).hexdigest()}
                for t in PROJECTION_TABLES}


class Corpus:
    def __init__(self, connection, index, source_id, audit=None):
        self.index = index; self.source_id = source_id; self.audit = audit
        self.writer = LabelWriter(connection)
        self.counts = Counter(); self.field_keys = Counter(); self.field_nonblank = Counter(); self.field_invalid = Counter()
        self.identity_fields = Counter(); self.multi_fields = Counter(); self.years = defaultdict(Counter)
        self.ids = set(); self.set_counts = Counter(); self.no_ndc_sets = set(); self.identified_sets = set()
        self.label_ndcs = set(); self.matched_ndcs = set(); self.unmatched_ndcs = set(); self.ambiguous_ndcs = set()
        self.blockers = defaultdict(list); self.rejected_candidates = Counter(); self.known = {}

    def process(self, raw, partition, ordinal):
        sid = raw.get("id"); set_id = raw.get("set_id")
        if type(sid) is not str or not sid.strip() or type(set_id) is not str or not set_id.strip():
            raise SourceError("Missing original label ID/set_id; replacements forbidden")
        if sid in self.ids:
            raise SourceError("Duplicate original label ID within corpus")
        self.ids.add(sid); self.set_counts[set_id] += 1; self.counts["source_labels"] += 1
        admission = self.index.admit(raw); of = raw.get("openfda") or {}
        effective, date_status = parse_effective(raw.get("effective_time")); version = parse_version(raw.get("version"))
        self.counts["date_status_" + date_status] += 1
        self.counts["source_nonnegative_integer_version"] += int(source_integer_version(raw.get("version")))
        self.counts["sqlite_integer_version_representable"] += int(version is not None)
        self.counts["version_outside_sqlite_integer_range"] += int(source_integer_version(raw.get("version")) and version is None)
        year = effective[:4] if effective else "UNKNOWN_DATE"; self.years[year]["total"] += 1
        self.years[year]["with_product_ndc"] += int(bool(admission["all_ndcs"]))
        for field in ("product_ndc", "package_ndc", "rxcui", "spl_id", "spl_set_id", "application_number", "substance_name", "brand_name", "generic_name"):
            values = of.get(field) or []
            self.identity_fields[field] += int(bool(values))
            self.multi_fields[field] += int(isinstance(values, list) and len(values) > 1)
        present = []; usable = []
        for field in FIELDS + (OPTIONAL_FIELD,):
            value = raw.get(field)
            is_present = field in raw
            good_shape = isinstance(value, str) or (isinstance(value, list) and all(isinstance(x, str) for x in value))
            nonblank = bool(value.strip()) if isinstance(value, str) else (any(x.strip() for x in value) if good_shape and isinstance(value, list) else False)
            self.field_keys[field] += int(is_present); self.field_nonblank[field] += int(nonblank)
            self.field_invalid[field] += int(is_present and not good_shape)
            if is_present and field in FIELDS: present.append(field)
            if nonblank and field in FIELDS: usable.append(field)
        self.counts["any_requested_field_present"] += int(bool(present))
        self.counts["any_requested_nonblank_text"] += int(bool(usable))
        self.counts["labels_without_requested_field"] += int(not present)
        self.counts["labels_without_usable_requested_text"] += int(not usable)
        self.label_ndcs.update(admission["all_ndcs"]); self.matched_ndcs.update(admission["matched"])
        self.unmatched_ndcs.update(admission["unmatched"])
        # Runtime ambiguity is distinct from conflicts flagged using the source universe.
        self.ambiguous_ndcs.update(v for v in admission["all_ndcs"] if len(self.index.ndcs.get(v, [])) > 1)
        if admission["all_ndcs"]:
            self.identified_sets.add(set_id); self.counts["with_product_ndc"] += 1
            self.counts["with_any_matching_ndc"] += int(bool(admission["matched"]))
            self.counts["all_ndcs_matched_regardless_flags"] += int(not admission["unmatched"])
            self.counts["no_matching_product_ndc"] += int(not admission["matched"])
            self.counts["naive_exactly_one_candidate"] += int(len(admission["candidates"]) == 1)
            self.counts["naive_multiple_candidates"] += int(len(admission["candidates"]) > 1)
        else:
            self.no_ndc_sets.add(set_id); self.counts["no_ndc_nonempty_openfda"] += int(bool(of))
        self.counts["primary_" + admission["reason"]] += 1
        self.counts["rejected_with_unmatched_ndc"] += int(bool(admission["unmatched"]))
        self.counts["rejected_with_conflicted_ndc"] += int(bool(admission["conflicted"]))
        self.counts["rejected_with_both_reasons"] += int(bool(admission["unmatched"]) and bool(admission["conflicted"]))
        if not admission["admitted"]:
            for pid in admission["candidates"]:
                self.rejected_candidates[pid] += 1
                self.blockers[(pid, set_id)].append({"version": version, "date": effective})
            label_id = None; pids = []
        else:
            label, sections = project_label(raw, self.source_id); label_id = label["label_id"]
            self.writer.put("labels", label)
            for section in sections: self.writer.put("label_sections", section)
            by_product = {}
            for ndc in admission["all_ndcs"]:
                edge = edge_projection(label, raw, admission, ndc, self.index)
                if edge["product_id"] in by_product:
                    prior = by_product[edge["product_id"]]
                    basis = json.loads(prior["verification_basis_json"])
                    basis.setdefault("matched_product_ndcs", [prior["matched_value"]]).append(ndc)
                    prior["verification_basis_json"] = canonical_json(basis)
                else:
                    by_product[edge["product_id"]] = edge
            for edge in by_product.values(): self.writer.put("product_labels", edge)
            pids = sorted(by_product)
            self.counts["clean_labels"] += 1; self.counts["clean_edges"] += len(pids)
            self.counts["clean_labels_without_requested_field"] += int(not present)
            self.counts["clean_labels_without_usable_requested_text"] += int(not usable)
            known_ids = {"f2ef667a-4871-4f28-a0b3-3f79fbbe180c", "0e853a5e-9eab-4bb6-803d-fd9b97e8b550", "2b1bf1d7-4399-46bd-8654-2590513da5c2"}
            if sid in known_ids or set(admission["all_ndcs"]).intersection({"50090-8027", "50090-6051", "50090-5949", "50090-5824"}):
                self.known[sid] = {"label_id": label_id, "source_record_id": sid, "set_id": set_id, "version": raw.get("version"),
                    "effective_time": raw.get("effective_time"), "product_ndcs": admission["all_ndcs"], "product_ids": pids,
                    "source_fields_present": present, "source_nonblank_fields": usable, "source_identity": of}
        if self.audit is not None:
            self.audit.write(canonical_json({"source_record_id": sid, "set_id": set_id, "version_raw": raw.get("version"),
                "effective_time_raw": raw.get("effective_time"), "date_status": date_status, "version_number": version,
                "version_parse_status": "SQLITE_INTEGER_RANGE_UNREPRESENTABLE" if source_integer_version(raw.get("version")) and version is None else ("VALID" if version is not None else "INVALID"),
                "partition": partition, "ordinal": ordinal,
                "reason": admission["reason"], "admitted": admission["admitted"], "label_id": label_id, "product_ids": pids,
                "all_product_ndcs": admission["all_ndcs"], "unmatched_product_ndcs": admission["unmatched"],
                "ambiguous_or_conflicted_product_ndcs": admission["conflicted"], "source_section_fields_present": present,
                "nonblank_requested_sections": usable}) + "\n")

    def report(self):
        duplicate_no_ndc_sets = sum(self.set_counts[s] != 1 for s in self.no_ndc_sets)
        return {"counts": dict(self.counts), "section_field_presence": dict(self.field_keys), "section_nonblank_text": dict(self.field_nonblank),
            "section_invalid_shapes": dict(self.field_invalid), "identity_field_presence": dict(self.identity_fields), "identity_multi_valued": dict(self.multi_fields),
            "effective_year_identity": {k: dict(v) for k, v in sorted(self.years.items())},
            "distinct_label_product_ndcs": len(self.label_ndcs), "distinct_matched_product_ndcs": len(self.matched_ndcs),
            "distinct_unmatched_product_ndcs": len(self.unmatched_ndcs), "distinct_runtime_ambiguous_product_ndcs": len(self.ambiguous_ndcs),
            "no_ndc_set_ids_shared_with_identified_labels": len(self.no_ndc_sets.intersection(self.identified_sets)),
            "no_ndc_set_ids_not_unique": duplicate_no_ndc_sets, "projection": self.writer.report()}


def finalize_selection(connection, corpus):
    groups = defaultdict(list)
    cursor = connection.execute("""SELECT pl.product_id,pl.label_id,l.set_id,l.version_number,l.effective_date,l.date_status,
        l.has_requested_safety_section,l.extraction_valid,pl.applicability_class,pl.ingredient_set_verified,
        pl.formulation_scope_verified,p.eligibility_mode,l.source_identity_json
        FROM product_labels pl JOIN labels l ON l.label_id=pl.label_id JOIN products p ON p.product_id=pl.product_id
        ORDER BY pl.product_id,l.set_id,pl.label_id""")
    # Section hashes, rather than full text, are enough for deterministic tie comparison.
    section_hashes = defaultdict(list)
    for lid, field, value_hash in connection.execute("SELECT label_id,source_field,source_value_sha256 FROM label_sections ORDER BY label_id,source_field"):
        section_hashes[lid].append([field, value_hash])
    for pid, lid, set_id, version, effective, status, has_text, extracted, cls, ingredients, formulation, mode, of in cursor:
        identity = json.loads(of)
        # Document UUID arrays differ between identical source versions, so exclude only those IDs.
        comparable_identity = {k: v for k, v in identity.items() if k not in {"spl_id", "spl_set_id"}}
        groups[(pid, set_id)].append({"label_id": lid, "version": version, "date": effective,
            "viable": cls == "EXACT_PRODUCT" and bool(ingredients) and bool(formulation) and status == "VALID" and version is not None and bool(has_text) and bool(extracted),
            "normal_consumer": mode == "NORMAL_CONSUMER", "selection_fingerprint": sha(canonical_json([section_hashes[lid], comparable_identity]))})
    decisions = Counter()
    for key, records in groups.items():
        selected = select_group(records, corpus.blockers.get(key, []))
        for lid, (status, consumer) in selected.items():
            connection.execute("UPDATE product_labels SET selection_status=?,consumer_eligible=? WHERE product_id=? AND label_id=?", (status, consumer, key[0], lid))
            decisions[status] += 1; decisions["consumer_eligible_edges"] += consumer
    return dict(decisions)


LABEL_LIMITATIONS = ["Stored label evidence is product-specific; not an ingredient-wide or complete safety assessment.",
    "No structured section in an inspected record establishes clinical absence of a warning, contraindication, adverse reaction or interaction.",
    "Dates and latest versions are bounded to the September 25, 2026 preserved export; not live availability or independent approval."]


def populate_label_coverage(connection, corpus):
    summaries = defaultdict(lambda: Counter())
    query = """SELECT pl.product_id,pl.applicability_class,pl.selection_status,pl.ingredient_set_verified,pl.formulation_scope_verified,
        l.has_requested_safety_section,l.date_status,l.extraction_valid FROM product_labels pl JOIN labels l ON l.label_id=pl.label_id"""
    for pid, cls, selection, ingredients, formulation, text, date_status, extracted in connection.execute(query):
        s = summaries[pid]; s["clean_labels"] += 1; s["usable_text"] += int(bool(text))
        s["ambiguous"] += int(cls == "AMBIGUOUS" or selection == "AMBIGUOUS")
        s["selected"] += int(selection == "SELECTED_STORED" and cls == "EXACT_PRODUCT" and ingredients and formulation and date_status == "VALID" and extracted)
        s["earlier"] += int(selection == "EARLIER_STORED")
        s["scope_or_date_gaps"] += int(not ingredients or not formulation or date_status != "VALID" or not extracted)
    states = Counter()
    for (pid,) in connection.execute("SELECT product_id FROM products ORDER BY product_id"):
        s = summaries.get(pid, Counter()); rejected = corpus.rejected_candidates[pid]
        if not s["clean_labels"]:
            state = "UNKNOWN"; reason = "STRICT_PRODUCT_NDC_REJECTION" if rejected else "NO_STORED_STRICT_PRODUCT_LABEL"
        elif not s["usable_text"]:
            state = "UNAVAILABLE"; reason = "NO_USABLE_STRUCTURED_SAFETY_TEXT_IN_STORED_LABEL"
        elif s["ambiguous"] and not s["selected"] and not s["earlier"]:
            state = "UNKNOWN"; reason = "LABEL_SCOPE_OR_VERSION_CONFLICT"
        elif s["selected"] and not (s["earlier"] or s["scope_or_date_gaps"] or s["ambiguous"] or rejected):
            state = "READY"; reason = "SELECTED_PRODUCT_SCOPED_STORED_LABEL"
        else:
            state = "PARTIAL"; reason = "STORED_LABEL_TEXT_WITH_SCOPE_DATE_OR_SELECTION_LIMITATIONS"
        states[state] += 1
        row = {"entity_type": "PRODUCT", "entity_id": pid, "product_id": pid, "domain": "labels", "window_key": "",
            "state": state, "reason_code": reason, "scope": "PRODUCT", "as_of_date": "2026-09-25", "source_date": "2026-09-25",
            "measured_count": s["clean_labels"] if state in {"READY", "PARTIAL"} else None,
            "unresolved_count": None if state == "UNKNOWN" and not rejected and not s["clean_labels"] else rejected + s["scope_or_date_gaps"] + s["ambiguous"], "rule_version": POLICY_VERSION,
            "limitations_json": canonical_json(LABEL_LIMITATIONS)}
        columns = [r[1] for r in connection.execute("PRAGMA table_info(coverage)")]
        old = connection.execute("SELECT 1 FROM coverage WHERE entity_type='PRODUCT' AND entity_id=? AND domain='labels' AND window_key=''", (pid,)).fetchone()
        if old:
            connection.execute("UPDATE coverage SET " + ",".join(c + "=?" for c in columns) + " WHERE entity_type='PRODUCT' AND entity_id=? AND domain='labels' AND window_key=''", [row.get(c) for c in columns] + [pid])
        else:
            connection.execute("INSERT INTO coverage (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")", [row.get(c) for c in columns])
    return dict(states)
