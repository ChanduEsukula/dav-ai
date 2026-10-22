"""Only the pinned enforcement partition and immutable Phase 3A parent."""
import json
from pathlib import Path

from .sources import InputTracker, SNAPSHOTS, SourceError, check_parquet

PARENT_PATH = "data/releases/dav_ai_pharma_v1/phase3-labels-2026-10-06/pharma.sqlite"
PARENT_SHA256 = "c4ed094c94e28c8fe1fa3e748bb0d976e04354e2dd28ca219d0eed7cf20c785f"
PARENT_BYTES = 3404451840
FOLDER = "data/research/enforcement/" + SNAPSHOTS["enforcement"]
PARTITION = FOLDER + "/files/quarter=enforcement/e7fd78d15d17540e65a1d93c"
PARQUET = PARTITION + "/enforcement.parquet"
SOURCE_NAME = "openfda_drug_enforcement"


def discover_recall_inputs(root):
    tracker = InputTracker(root)
    parent = tracker.inspect(PARENT_PATH, hash_now=True, recorded_sha256=PARENT_SHA256)
    metadata = tracker.json(str(Path(PARENT_PATH).parent / "release_metadata.json"))
    if parent.stat().st_size != PARENT_BYTES or parent.stat().st_mode & 0o222 or metadata["database_sha256"] != PARENT_SHA256 or metadata["database_bytes"] != PARENT_BYTES:
        raise SourceError("Frozen Phase 3A parent mismatch")
    tracker.inspect(metadata["parent_release_path"], hash_now=True, recorded_sha256=metadata["parent_release_sha256"])
    tracker.inspect("docs/pharma_release_v1_contract.md", hash_now=True)
    snapshot = tracker.json(FOLDER + "/snapshot.json")
    summary = tracker.json(FOLDER + "/summary.json")
    dataset = tracker.json(FOLDER + "/manifest.json")["results"]["drug"]["enforcement"]
    receipt = tracker.json(PARTITION + "/receipt.json")
    if (snapshot["dataset_key"] != SNAPSHOTS["enforcement"] or summary["dataset_key"] != SNAPSHOTS["enforcement"]
            or not summary["complete"] or summary["raw_records"] != 17975 or summary["quarantined"] != 1
            or summary["failures"] or summary["files_complete"] != 1 or summary["export_date"] != "2026-09-25"
            or dataset["total_records"] != 17975 or dataset["export_date"] != "2026-09-25" or len(dataset["partitions"]) != 1
            or summary["observed_at"] != snapshot["observed_at"] or snapshot["observed_at"][:10] != "2026-09-26"
            or receipt["records"] != 17975 or receipt["valid_records"] != 17974 or receipt["quarantined"] != 1
            or receipt["url"] != dataset["partitions"][0]["file"]):
        raise SourceError("Pinned enforcement snapshot mismatch")
    measured = check_parquet(tracker, PARQUET, {k: "string" for k in ("source_id", "source_url", "export_date", "observed_at", "raw_json")}, 17974, receipt["outputs"]["enforcement.parquet"])
    quarantine = tracker.inspect(PARTITION + "/quarantine.jsonl", hash_now=True, recorded_sha256=receipt["outputs"]["quarantine.jsonl"])
    quarantined = [json.loads(line) for line in quarantine.read_text().splitlines() if line]
    if len(quarantined) != 1 or quarantined[0]["error"] != "Missing source identity" or quarantined[0]["raw"]["recall_number"] != "":
        raise SourceError("Quarantine accounting mismatch")
    return tracker, metadata, {"snapshot": snapshot, "summary": summary, "dataset": dataset, "receipt": receipt,
        "parquet": measured, "quarantine": quarantined,
        "quarter": "enforcement", "quarter_basis": "Hive partition path; absent from physical Parquet schema"}


def stream_enforcement(path):
    import pyarrow.parquet as pq
    for batch in pq.ParquetFile(path).iter_batches(batch_size=1024):
        for envelope in batch.to_pylist():
            yield envelope | {"quarter": "enforcement"}
