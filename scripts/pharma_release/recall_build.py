"""Lossless recall projection, audited admissions and collision-safe replay."""
from collections import Counter
from datetime import datetime
import hashlib
import json

from .ids import qualified_id, require_identifier
from .recall_applicability import RULE_VERSION
from .recall_sources import SOURCE_NAME
from .sources import canonical_json, SourceError

PROJECTION_TABLES = ("recalls", "product_recalls", "coverage")
LIMITATIONS = ["Recall linkage/discovery coverage is partial; absence of an edge is not proof of no historical recalls.",
    "Only explicit NDC-marked text is resolved against the frozen current identity snapshot; historical/unmatched/ambiguous identifiers are held back.",
    "FDA classification and status are as reported in the 2026-09-25 source snapshot; not live current status.",
    "Exact code_info and more_code_info are retained; lot scope is unparsed UNKNOWN, never an assertion that the user's package or all lots are affected."]


def parse_date(value):
    if type(value) is not str or len(value) != 8 or not value.isascii() or not value.isdigit():
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def project_recall(envelope, source_id, admission):
    raw = json.loads(envelope["raw_json"])
    original = require_identifier(raw.get("recall_number"))
    if envelope["source_id"] != original:
        raise SourceError("Envelope ID does not equal original recall number")
    for field in ("product_description", "reason_for_recall"):
        if type(raw.get(field)) is not str:
            raise SourceError("Missing/invalid required recall field: " + field)
    row = {"recall_id": qualified_id("recall", SOURCE_NAME, original), "source_id": source_id,
        "source_record_id": original, "recall_number": original,
        "source_content_sha256": hashlib.sha256(envelope["raw_json"].encode()).hexdigest(),
        "source_identity_json": canonical_json({"raw_record": raw, "raw_json": envelope["raw_json"],
            "envelope": {k: v for k, v in envelope.items() if k != "raw_json"},
            "applicability": {k: v for k, v in admission.items() if k != "matches_by_product"}})}
    for field in ("event_id", "product_description", "reason_for_recall", "classification", "recalling_firm", "distribution_pattern", "code_info"):
        row[field] = raw.get(field)
    row["source_reported_status"] = raw.get("status")
    for field in ("recall_initiation_date", "report_date"):
        row[field + "_raw"] = raw.get(field)
        row[field] = parse_date(raw.get(field))
    return row


class RecallWriter:
    def __init__(self, connection):
        self.connection = connection
        self.columns = {t: [r[1] for r in connection.execute(f"PRAGMA table_info({t})")] for t in PROJECTION_TABLES}
        self.keys = {t: [r[1] for r in sorted(connection.execute(f"PRAGMA table_info({t})"), key=lambda r: r[5]) if r[5]] for t in PROJECTION_TABLES}
        self.hashes = {t: [] for t in PROJECTION_TABLES}
        self.inserted = Counter(); self.replayed = Counter()

    def put(self, table, row):
        columns = self.columns[table]; keys = self.keys[table]
        values = [row.get(k) for k in columns]
        old = self.connection.execute(f"SELECT {','.join(columns)} FROM {table} WHERE " + " AND ".join(k + "=?" for k in keys), [row[k] for k in keys]).fetchone()
        if old is None:
            self.connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
            self.inserted[table] += 1
        elif list(old) != values:
            raise SourceError("Nonidentical replay/collision in " + table)
        else:
            self.replayed[table] += 1
        self.hashes[table].append(hashlib.sha256(canonical_json(values).encode()).digest())

    def report(self):
        return {t: {"projected_rows": len(self.hashes[t]), "inserted": self.inserted[t], "identical_replays": self.replayed[t],
            "sha256_sorted_row_hashes": hashlib.sha256(b"".join(sorted(self.hashes[t]))).hexdigest()} for t in PROJECTION_TABLES}


def coverage_row(entity_type, identifier, count, unresolved=0):
    positive = count > 0
    return {"entity_type": entity_type, "entity_id": identifier, entity_type.lower() + "_id": identifier,
        "domain": "recalls", "window_key": "", "state": "PARTIAL" if positive else "UNKNOWN",
        "reason_code": "VERIFIED_POSITIVE_IN_INCOMPLETE_COLLECTION" if positive else "NO_VERIFIED_RECALL_LINK",
        "scope": "EXPLICIT_TEXT_NDC_PRODUCT_APPLICABILITY; FROZEN_2026-09-26_IDENTITY; ENFORCEMENT_EXPORT_2026-09-25",
        "as_of_date": "2026-09-26", "source_date": "2026-09-25", "measured_count": count if positive else None,
        "unresolved_count": unresolved if entity_type == "RECALL" else None, "rule_version": RULE_VERSION,
        "limitations_json": canonical_json(LIMITATIONS + (["No verified recall is linked to this product in this release. Recall coverage is partial."] if not positive and entity_type == "PRODUCT" else []))}


class RecallCorpus:
    def __init__(self, connection, index, source_id, audit=None, expected_envelope=None):
        self.index = index; self.source_id = source_id; self.audit = audit; self.expected_envelope = expected_envelope or {}
        self.writer = RecallWriter(connection); self.counts = Counter(); self.ids = set()
        self.method_counts = Counter(); self.ndc_resolutions = Counter(); self.field_presence = Counter(); self.date_status = Counter()

    def process(self, envelope, ordinal):
        if any(envelope.get(k) != value for k, value in self.expected_envelope.items()):
            raise SourceError("Pinned source envelope vintage/provenance mismatch")
        raw = json.loads(envelope["raw_json"]); original = require_identifier(raw.get("recall_number"))
        if original in self.ids:
            raise SourceError("Duplicate recall identity in usable source corpus")
        self.ids.add(original); self.counts["usable_records"] += 1
        self.field_presence.update(raw.keys())
        admission = self.index.admit(raw); self.counts[admission["category"]] += 1
        self.counts["RECALLS_WITH_OVERLONG_NDC_TOKEN_FRAGMENT"] += int(any(o["parser_match_followed_by_digit"] for o in admission["occurrences"]))
        self.counts["HAS_EXPLICIT_TEXT_NDC"] += int(bool(admission["occurrences"]))
        ndcs = {o["text_ndc"] for o in admission["occurrences"]}
        outcomes = {(o["text_ndc"], o["resolution"]) for o in admission["occurrences"]}
        self.ndc_resolutions.update(state for _, state in outcomes)
        of = raw.get("openfda") or {}; packages = of.get("package_ndc") or []; products = of.get("product_ndc") or []
        self.counts["HAS_OPENFDA_NDC" if packages or products else "NO_OPENFDA_NDC"] += 1
        if ndcs and (packages or products):
            self.counts["TEXT_MATCHES_OPENFDA_PACKAGE" if ndcs.intersection(packages) else "TEXT_OPENFDA_DISAGREE"
                if not {"-".join(v.split("-")[:2]) for v in ndcs}.intersection(products) else "TEXT_MATCHES_OPENFDA_PRODUCT_ONLY"] += 1
        self.counts["RECALLS_WITH_AT_LEAST_ONE_CLEAN_PRODUCT"] += int(bool(admission["matches_by_product"]))
        self.counts["RECALLS_RESOLVING_TO_ONE_PRODUCT"] += int(len(admission["matches_by_product"]) == 1)
        self.counts["RECALLS_RESOLVING_TO_MULTIPLE_PRODUCTS"] += int(len(admission["matches_by_product"]) > 1)
        self.counts["PARTIAL_RECALLS_WITH_CLEAN_EDGES"] += int(admission["partial"])
        row = project_recall(envelope, self.source_id, admission); self.writer.put("recalls", row)
        for field in ("recall_initiation_date", "report_date"):
            self.date_status[field + ("_VALID" if row[field] else "_MISSING" if raw.get(field) is None else "_INVALID")] += 1
        for pid in sorted(admission["matches_by_product"]):
            edge = self.index.edge(pid, row["recall_id"], raw, admission)
            self.writer.put("product_recalls", edge); self.method_counts[edge["match_method"]] += 1
            self.counts["TOTAL_RECALL_PRODUCT_EDGES"] += 1
        self.writer.put("coverage", coverage_row("RECALL", row["recall_id"], len(admission["matches_by_product"]),
            len({o["text_ndc"] for o in admission["unresolved"]})))
        if self.audit:
            self.audit.write(canonical_json({"ordinal": ordinal, "recall_number": original, "recall_id": row["recall_id"],
                "source_content_sha256": row["source_content_sha256"], "category": admission["category"],
                "partial": admission["partial"], "occurrences": admission["occurrences"],
                "admitted_product_ids": sorted(admission["matches_by_product"]), "unresolved": admission["unresolved"]}) + "\n")

    def finalize_coverage(self):
        linked = dict(self.writer.connection.execute("SELECT product_id,count(*) FROM product_recalls GROUP BY product_id"))
        for (pid,) in self.writer.connection.execute("SELECT product_id FROM products ORDER BY product_id"):
            self.writer.put("coverage", coverage_row("PRODUCT", pid, linked.get(pid, 0)))

    def report(self):
        return {"counts": dict(sorted(self.counts.items())), "all_class_precedence_methods": dict(sorted(self.method_counts.items())),
            "distinct_identifier_resolution_counts_per_recall": dict(self.ndc_resolutions), "source_field_presence": dict(self.field_presence),
            "date_status": dict(self.date_status), "projection": self.writer.report()}
