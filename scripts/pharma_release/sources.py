"""Bounded, offline source discovery with explicit hash and date provenance.

No production imports, PostgreSQL connections, network, or source-directory
creation. Phase 1 checks metadata/Parquet footers and hashes small selected inputs;
large ZIP/DuckDB/dump hashes are explicitly deferred, never represented as fresh.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile

from .ids import qualified_id

LABEL_CACHE = "data/pharma_bulk_cache/3f2a00b793176b411f8df071f43e1df07e08b995c3c0db8b274660dead854d0c"
SNAPSHOTS = {
    "ndc": "f8e9d4ca399d61b788ad5dc51d7adad1d2d99d32b02e3ca8a2e02821702b44d5",
    "enforcement": "4fd1a8f0f22892252966e6d5923d8d8a03c8d697c9050bfddfaa2fd25f91f9e2",
}
EVIDENCE = "docs/evidence/pharma-release-v1-2026-10-06"


class SourceError(ValueError):
    """A pinned input/fixture/schema failed; do not substitute another source."""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_file(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SourceError("Missing or outside-repository input: " + str(relative))
    return path


class InputTracker:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.records = {}

    def inspect(self, relative, *, hash_now=False, recorded_sha256=None):
        path = repo_file(self.root, relative)
        stat = path.stat()
        key = path.relative_to(self.root).as_posix()
        if recorded_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", recorded_sha256):
            raise SourceError("Invalid recorded SHA256")
        saved = self.records.get(key)
        if saved:
            if (saved["bytes"], saved["mtime_ns"]) != (stat.st_size, stat.st_mtime_ns):
                raise SourceError("Input changed during discovery: " + key)
            if recorded_sha256 and saved["recorded_sha256"] and recorded_sha256 != saved["recorded_sha256"]:
                raise SourceError("Conflicting recorded SHA256: " + key)
            if hash_now and saved["sha256"] is None:
                saved["sha256"] = file_sha256(path)
                saved["verification_basis"] = "FRESH_SHA256"
            expected = recorded_sha256 or saved["recorded_sha256"]
            if saved["sha256"] and expected and saved["sha256"] != expected:
                raise SourceError("SHA256 mismatch: " + key)
            if recorded_sha256:
                saved["recorded_sha256"] = recorded_sha256
            self.assert_unchanged()
            return path
        fresh = file_sha256(path) if hash_now else None
        if fresh and recorded_sha256 and fresh != recorded_sha256:
            raise SourceError("SHA256 mismatch: " + key)
        self.records[key] = {
            "path": key, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "sha256": fresh, "recorded_sha256": recorded_sha256,
            "verification_basis": "FRESH_SHA256" if fresh else "SIZE_MTIME_ONLY_RECORDED_HASH_NOT_REVERIFIED",
        }
        self.assert_unchanged()
        return path

    def json(self, relative):
        path = self.inspect(relative, hash_now=True)
        return json.loads(path.read_text())

    def assert_unchanged(self):
        for key, saved in self.records.items():
            path = repo_file(self.root, key)
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (saved["bytes"], saved["mtime_ns"]):
                raise SourceError("Protected input changed: " + key)


@dataclass(frozen=True)
class Source:
    source_id: str
    source_name: str
    capture_id: str
    source_kind: str
    input_paths: tuple
    expected_rows: int | None
    source_url: str | None = None
    parent_source_id: str | None = None
    export_date: str | None = None
    observed_at: str | None = None
    captured_at: str | None = None
    ingested_at: str | None = None
    transform_version: str | None = None

    def sqlite_row(self, tracker):
        values = asdict(self)
        paths = values.pop("input_paths")
        values.pop("expected_rows")
        inputs = [tracker.records[p] for p in paths]
        values["verification_basis"] = "PER_INPUT: fresh SHA256 where present; other source bytes not freshly verified"
        values["inputs_json"] = canonical_json(inputs)
        return values


@dataclass
class Catalog:
    sources: tuple
    tracker: InputTracker
    measurements: dict
    notes: tuple

    def report(self):
        self.tracker.assert_unchanged()
        return {"sources": [asdict(s) for s in self.sources],
                "inputs": list(self.tracker.records.values()), "measurements": self.measurements,
                "notes": list(self.notes), "protected_inputs_size_mtime_unchanged": True}


def check_parquet(tracker, relative, expected_types, expected_rows, recorded_hash=None):
    import pyarrow.parquet as pq
    path = tracker.inspect(relative, hash_now=True, recorded_sha256=recorded_hash)
    file = pq.ParquetFile(path)
    actual = {field.name: str(field.type) for field in file.schema_arrow}
    if actual != expected_types or file.metadata.num_rows != expected_rows:
        raise SourceError(f"Parquet schema/row mismatch: {relative}: {actual}, {file.metadata.num_rows}")
    return {"rows": file.metadata.num_rows, "schema": actual}


def discover_sources(root):
    tracker = InputTracker(root)
    contract = tracker.inspect("docs/pharma_release_v1_contract.md", hash_now=True)
    if "Contract ID: `dav-ai-pharma-release-v1`" not in contract.read_text() or "Policy version: `1.0.0`" not in contract.read_text():
        raise SourceError("Unsupported contract identity/policy")
    for path in sorted((tracker.root / EVIDENCE).iterdir()):
        if path.is_file():
            tracker.inspect(path.relative_to(tracker.root), hash_now=True)
    eligibility = tracker.json(EVIDENCE + "/product_eligibility_counts.json")
    label_fixture = tracker.json(EVIDENCE + "/label_section_coverage.json")
    if eligibility["counts"] != {"NORMAL_CONSUMER": 95426, "REGULATORY_ONLY": 21315, "EXCLUDED_V1": 21518}:
        raise SourceError("Step 1 eligibility fixture mismatch")
    if eligibility["combination_counts"] != {"NORMAL_CONSUMER": 17202, "REGULATORY_ONLY": 5932, "EXCLUDED_V1": 1205} or eligibility["normal_consumer_identity_partial_flags"]["identity_partial_candidates"] != 2856:
        raise SourceError("Step 1 combination/partial fixture mismatch")
    expected_label = {"total_labels": 262887, "boxed_warning_present": 33146,
        "warnings_and_cautions_present": 47047, "warnings_present": 204699,
        "contraindications_present": 89729, "adverse_reactions_present": 91861,
        "drug_interactions_present": 68722, "any_requested_safety_section": 252671,
        "effective_date_valid": 262881, "effective_date_after_export": 9}
    if any(label_fixture["totals"].get(k) != v for k, v in expected_label.items()):
        raise SourceError("Step 1 label fixture mismatch")
    sources = []
    measurements = {"step1_eligibility_expected": eligibility, "step1_label_expected": expected_label}
    raw_type = {name: "string" for name in ("source_id", "source_url", "export_date", "observed_at", "raw_json")}
    for kind, key in SNAPSHOTS.items():
        pointer = tracker.json(f"data/research/{kind}-latest.json")
        folder = f"data/research/{kind}/{key}"
        if pointer != {"snapshot_path": folder, "dataset_key": key}:
            raise SourceError("Pinned source pointer changed: " + kind)
        meta = tracker.json(folder + "/snapshot.json")
        summary = tracker.json(folder + "/summary.json")
        manifest = tracker.json(folder + "/manifest.json")["results"]["drug"][kind]
        expected = 138259 if kind == "ndc" else 17974
        source_total = 138259 if kind == "ndc" else 17975
        expected_date = "2026-09-26" if kind == "ndc" else "2026-09-25"
        if meta["dataset_key"] != key or summary["dataset_key"] != key or not summary["complete"] or manifest["export_date"] != expected_date or manifest["total_records"] != source_total:
            raise SourceError("Snapshot metadata mismatch: " + kind)
        if meta["observed_at"][:10] != "2026-09-26" or summary["observed_at"] != meta["observed_at"]:
            raise SourceError("Pinned source observation date mismatch: " + kind)
        paths = sorted((tracker.root / folder).glob(f"files/quarter=*/*/{kind}.parquet"))
        if len(paths) != 1 or len(manifest["partitions"]) != 1:
            raise SourceError("Unexpected pinned partition layout: " + kind)
        relative = paths[0].relative_to(tracker.root).as_posix()
        receipt = tracker.json(paths[0].parent.relative_to(tracker.root) / "receipt.json")
        if receipt["valid_records"] != expected or receipt["records"] != source_total or receipt["url"] != manifest["partitions"][0]["file"]:
            raise SourceError("Source receipt mismatch: " + kind)
        measurements[kind] = check_parquet(tracker, relative, raw_type, expected, receipt["outputs"][kind + ".parquet"])
        measurements[kind]["quarantined_records"] = receipt["quarantined"]
        tracker.inspect(paths[0].parent.relative_to(tracker.root) / "quarantine.jsonl", hash_now=True,
                        recorded_sha256=receipt["outputs"]["quarantine.jsonl"])
        name = "openfda_ndc_directory" if kind == "ndc" else "openfda_drug_enforcement"
        sources.append(Source(qualified_id("source", name, key), name, key, "RAW_SNAPSHOT",
            (relative,), expected, receipt["url"], export_date=expected_date,
            observed_at=meta["observed_at"], captured_at=receipt["download"]["downloaded_at"], transform_version=meta["transform"]))
    identity_summary = tracker.json("data/research/identity/summary.json")
    mapping_path = tracker.inspect("data/research/identity/mapping.json.gz", hash_now=True)
    with gzip.open(mapping_path, "rt") as f:
        mapping = json.load(f)
    upstream_mapping_hash = hashlib.sha256(json.dumps(mapping, sort_keys=True, default=str).encode()).hexdigest()
    if upstream_mapping_hash != identity_summary["mapping_hash"] or mapping["source_dataset_key"] != SNAPSHOTS["ndc"] or identity_summary["observed_at"][:10] != "2026-09-26":
        raise SourceError("Identity mapping/vintage mismatch")
    identity_types = {
        "ingredients": {k: "string" for k in ("ingredient_id", "canonical_name", "source", "identity_rule", "observed_at")},
        "products": {**{k: "string" for k in ("source_id", "formulation_id", "generic_name", "brand_name", "labeler_name", "source_url", "observed_at")},
                     **{k: "list<element: string>" for k in ("ingredient_ids", "product_ndcs", "package_ndcs", "rxcuis")}},
        "formulations": {**{k: "string" for k in ("formulation_id", "strengths_json", "dosage_form")},
                         **{k: "list<element: string>" for k in ("ingredient_ids", "routes")}},
    }
    identity_paths = []
    for name, rows in (("ingredients", 7733), ("products", 138259), ("formulations", 34344)):
        relative = "data/research/identity/" + name + ".parquet"
        measurements[name] = check_parquet(tracker, relative, identity_types[name], rows)
        identity_paths.append(relative)
    sources.append(Source(qualified_id("source", "openfda_ndc_directory", "identity:" + upstream_mapping_hash),
        "openfda_ndc_directory", "identity:" + upstream_mapping_hash, "DERIVED", tuple(identity_paths), None,
        parent_source_id=sources[0].source_id, observed_at=identity_summary["observed_at"], transform_version="research-identity-exact-name-v1"))
    manifest_path = LABEL_CACHE + "/manifest.json"
    label_manifest = tracker.json(manifest_path)["results"]["drug"]["label"]
    if label_fixture["cache"] != LABEL_CACHE or label_manifest["export_date"] != "2026-09-25" or label_manifest["total_records"] != 262887 or len(label_manifest["partitions"]) != 14:
        raise SourceError("Pinned label manifest mismatch")
    if tracker.records[manifest_path]["sha256"] != label_fixture["manifest_sha256"]:
        raise SourceError("Label manifest differs from Step 1")
    label_paths = []
    capture_times = []
    for part in label_manifest["partitions"]:
        relative = LABEL_CACHE + "/" + Path(part["file"]).name
        if not relative.endswith(".json.zip"):
            raise SourceError("Unexpected label partition filename")
        receipt = tracker.json(relative.removesuffix(".zip") + ".receipt.json")
        path = tracker.inspect(relative, recorded_sha256=receipt["sha256"])
        if receipt["url"] != part["file"] or path.stat().st_size != receipt["bytes"] or receipt["downloaded_at"][:10] != "2026-09-26":
            raise SourceError("Label receipt mismatch")
        fixture_part = next((p for p in label_fixture["partitions"] if p["path"] == relative), None)
        if fixture_part is None or fixture_part["records"] != part["records"] or fixture_part["recorded_sha256"] != receipt["sha256"]:
            raise SourceError("Label partition differs from Step 1")
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != 1 or not members[0].filename.endswith(".json"):
                raise SourceError("Unexpected label ZIP member layout")
        label_paths.append(relative)
        capture_times.append(receipt["downloaded_at"])
    if sum(p["records"] for p in label_manifest["partitions"]) != 262887:
        raise SourceError("Label manifest partition total mismatch")
    sources.append(Source(qualified_id("source", "openfda_drug_label", LABEL_CACHE.split("/")[-1]),
        "openfda_drug_label", LABEL_CACHE.split("/")[-1], "RAW_SNAPSHOT", tuple(label_paths), 262887,
        "https://api.fda.gov/drug/label.json", export_date="2026-09-25", captured_at=max(capture_times)))
    analysis = tracker.json("data/research/analysis-summary.json")
    event = tracker.json("data/research/event-latest.json")
    event_summary = tracker.json(event["snapshot_path"] + "/summary.json")
    if event_summary["dataset_key"] != event["dataset_key"] or not event_summary["complete"]:
        raise SourceError("Incomplete or conflicting preserved AE source snapshot")
    db_path = tracker.inspect("data/research/analysis.duckdb")
    with readonly_analytics(db_path) as c:
        monthly = {row[0]: row[1] for row in c.execute("DESCRIBE monthly").fetchall()}
        required = {"ingredient_id": "VARCHAR", "reaction": "VARCHAR", "period": "DATE", "report_count": "BIGINT"}
        if any(monthly.get(k) != v for k, v in required.items()):
            raise SourceError("Existing monthly schema differs materially")
    capture_id = canonical_json([event["dataset_key"], upstream_mapping_hash, analysis["analysis_code_sha256"]])
    sources.append(Source(qualified_id("source", "openfda_drug_event", capture_id), "openfda_drug_event", capture_id,
        "DERIVED", ("data/research/analysis.duckdb", "data/research/analysis-summary.json"), None,
        "https://api.fda.gov/drug/event.json", export_date=event_summary["export_date"], observed_at=event_summary["observed_at"],
        transform_version=analysis["analysis_code_sha256"]))
    config_path = "backend/app/config/safety_communications.json"
    config = tracker.json(config_path)
    if len(config["communications"]) != 3 or any(e.get("scope") != "generic" or not e.get("names") for e in config["communications"]):
        raise SourceError("Preserved communication configuration mismatch")
    dump_path = "data/pharma_recovery/davai_recovery.dump"
    tracker.inspect(dump_path)
    dump_stat = tracker.records[dump_path]
    capture_id = canonical_json([dump_path, str(dump_stat["bytes"]), str(dump_stat["mtime_ns"]), tracker.records[config_path]["sha256"]])
    sources.append(Source(qualified_id("source", "fda_drug_safety_communications", capture_id),
        "fda_drug_safety_communications", capture_id, "CAPTURE", (dump_path, config_path), None,
        "https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications"))
    tracker.inspect("data/releases/dav_ai_v1/semaglutide/semaglutide_snapshot.json", hash_now=True)
    tracker.assert_unchanged()
    notes = (
        "Phase 1 checks footers/metadata, not identity ingestion, section extraction, applicability, or AE aggregation.",
        "Existing recall classifier is metadata-association only under v1; cannot authorize consumer edges.",
        "Existing normalizer omits cautions/adverse reactions; raw label cache is authoritative for future extraction.",
        "Communication config is not article text; dump capture dates remain NULL until preserved rows are read in Phase 7.",
        "Large ZIP/DuckDB/dump SHA256 verification is deferred; size/mtime and recorded archive hashes are distinguished.",
        "Consumer/runtime tables omit excluded products, so 138259 is the input reconciliation count; expected retained products are 116741.",
    )
    return Catalog(tuple(sources), tracker, measurements, notes)


@contextmanager
def readonly_analytics(path):
    import duckdb
    path = Path(path).resolve()
    if not path.is_file():
        raise SourceError("Missing analytics database")
    before = (path.stat().st_size, path.stat().st_mtime_ns)
    c = duckdb.connect(str(path), read_only=True)
    try:
        c.execute("SET memory_limit='512MB'")
        c.execute("SET max_temp_directory_size='0B'")
        c.execute("SET threads=1")
        yield c
    finally:
        c.close()
        if (path.stat().st_size, path.stat().st_mtime_ns) != before:
            raise SourceError("Research database changed")


def register_sources(connection, catalog):
    """Explicit provenance inserts only; no identity/evidence ingestion."""
    with connection:
        for source in catalog.sources:
            row = source.sqlite_row(catalog.tracker)
            columns = list(row)
            connection.execute("INSERT INTO sources (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")",
                               [row[c] for c in columns])
