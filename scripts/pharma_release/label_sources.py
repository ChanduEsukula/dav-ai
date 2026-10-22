"""Targeted pinned label/parent discovery only; no other research feed access."""
from pathlib import Path
import json
import zipfile

from .sources import InputTracker, LABEL_CACHE, SourceError

PARENT_PATH = "data/releases/dav_ai_pharma_v1/phase2-2026-10-06/pharma.sqlite"
PARENT_SHA256 = "cb89bb5c19b7df39873f7a1de30aeccee3c3479bb8f25aa2be73c1be83e0ef6a"
PARENT_BYTES = 823263232


def discover_label_inputs(root):
    tracker = InputTracker(root)
    parent = tracker.inspect(PARENT_PATH, hash_now=True, recorded_sha256=PARENT_SHA256)
    if parent.stat().st_size != PARENT_BYTES:
        raise SourceError("Pinned Phase 2 size mismatch")
    metadata = tracker.json(str(Path(PARENT_PATH).parent / "release_metadata.json"))
    if metadata["database_sha256"] != PARENT_SHA256 or metadata["database_bytes"] != PARENT_BYTES:
        raise SourceError("Pinned Phase 2 metadata mismatch")
    tracker.inspect("docs/pharma_release_v1_contract.md", hash_now=True)
    tracker.inspect("docs/evidence/pharma-release-v1-build-2026-10-06-phase1/schema.sql", hash_now=True)
    tracker.inspect("docs/evidence/pharma-release-v1-build-2026-10-06-phase2/schema.sql", hash_now=True)
    dataset = tracker.json(LABEL_CACHE + "/manifest.json")["results"]["drug"]["label"]
    if dataset["total_records"] != 262887 or dataset["export_date"] != "2026-09-25" or len(dataset["partitions"]) != 14:
        raise SourceError("Pinned label corpus metadata mismatch")
    parts = []
    for ordinal, part in enumerate(dataset["partitions"], 1):
        filename = f"drug-label-{ordinal:04d}-of-0014.json.zip"
        relative = LABEL_CACHE + "/" + filename
        if Path(part["file"]).name != filename:
            raise SourceError("Unexpected pinned label partition ordering")
        receipt_path = relative.removesuffix(".zip") + ".receipt.json"
        receipt = tracker.json(receipt_path)
        if receipt["url"] != part["file"] or receipt["downloaded_at"][:10] != "2026-09-26":
            raise SourceError("Pinned receipt capture mismatch")
        path = tracker.inspect(relative, hash_now=True, recorded_sha256=receipt["sha256"])
        if path.stat().st_size != receipt["bytes"]:
            raise SourceError("Pinned ZIP byte size mismatch")
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != 1 or not members[0].filename.endswith(".json"):
                raise SourceError("Unexpected label ZIP layout")
        parts.append({"path": relative, "receipt_path": receipt_path, "records": part["records"],
                      "sha256": receipt["sha256"], "source_url": part["file"], "captured_at": receipt["downloaded_at"]})
    if sum(p["records"] for p in parts) != 262887:
        raise SourceError("Label partition record totals differ")
    tracker.assert_unchanged()
    return tracker, metadata, dataset, parts


def stream_partition(path):
    import ijson
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) != 1:
            raise SourceError("Unexpected ZIP member layout")
        with archive.open(members[0]) as stream:
            # Reading through EOF validates the ZIP member CRC, without extraction.
            yield from ijson.items(stream, "results.item", use_float=True)
            while stream.read(1024 * 1024):
                pass
