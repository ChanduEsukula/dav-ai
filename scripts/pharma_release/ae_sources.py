"""Targeted, read-only research snapshot and frozen parent discovery."""
import json
from pathlib import Path

from .sources import InputTracker, SourceError

PARENT_PATH = "data/releases/dav_ai_pharma_v1/phase3b-recalls-2026-10-06/pharma.sqlite"
PARENT_SHA256 = "c0ffe8e77e94c7f4775ca22d60256800532b89b08c962801bcc81816c13ae61f"
PARENT_BYTES = 4108087296
RESEARCH_PATH = "data/research/analysis.duckdb"
RESEARCH_SHA256 = "1c2e0730636c39e17c4821ab5dc9690b0400534a4fce0278b324236e95d5e5d2"
SUMMARY_PATH = "data/research/analysis-summary.json"
SOURCE_NAME = "openfda_drug_event"
REQUIRED_COLUMNS = {
    "latest_reports": {"report_uid": "VARCHAR", "case_id": "VARCHAR", "first_received": "VARCHAR", "last_received": "VARCHAR",
        **{name: "BOOLEAN" for name in ("serious", "death", "hospitalization", "disability", "life_threatening")}},
    "report_ingredients": {"report_uid": "VARCHAR", "ingredient_id": "VARCHAR", **{name: "BOOLEAN" for name in ("suspect", "concomitant", "interacting")}},
    "report_reactions": {"report_uid": "VARCHAR", "reaction": "VARCHAR"},
    "monthly": {"ingredient_id": "VARCHAR", "reaction": "VARCHAR", "period": "DATE", "report_count": "BIGINT"}}


def discover_ae_inputs(root, parent):
    tracker = InputTracker(root)
    file = tracker.inspect(PARENT_PATH, hash_now=True, recorded_sha256=PARENT_SHA256)
    metadata = tracker.json(str(Path(PARENT_PATH).parent / "release_metadata.json"))
    if file.stat().st_size != PARENT_BYTES or file.stat().st_mode & 0o222 or metadata["database_sha256"] != PARENT_SHA256:
        raise SourceError("Frozen Phase 3B mismatch")
    prior_meta = tracker.json(str(Path(metadata["parent_release_path"]).parent / "release_metadata.json"))
    tracker.inspect(metadata["parent_release_path"], hash_now=True, recorded_sha256=metadata["parent_release_sha256"])
    tracker.inspect(prior_meta["parent_release_path"], hash_now=True, recorded_sha256=prior_meta["parent_release_sha256"])
    tracker.inspect("docs/pharma_release_v1_contract.md", hash_now=True)
    cursor = parent.execute("SELECT * FROM sources WHERE source_name=?", (SOURCE_NAME,))
    row = cursor.fetchone()
    if row is None: raise SourceError("Parent AE provenance missing")
    source = dict(zip([field[0] for field in cursor.description], row))
    pinned = {record["path"]: record for record in json.loads(source["inputs_json"])}
    if RESEARCH_PATH not in pinned or SUMMARY_PATH not in pinned: raise SourceError("Parent research lineage missing")
    research = tracker.inspect(RESEARCH_PATH, hash_now=True, recorded_sha256=RESEARCH_SHA256)
    stat = research.stat()
    if (stat.st_size, stat.st_mtime_ns) != (pinned[RESEARCH_PATH]["bytes"], pinned[RESEARCH_PATH]["mtime_ns"]):
        raise SourceError("Research snapshot differs from frozen lineage")
    tracker.inspect(SUMMARY_PATH, hash_now=True, recorded_sha256=pinned[SUMMARY_PATH]["sha256"])
    summary = tracker.json(SUMMARY_PATH)
    return tracker, metadata, source, summary


def open_research(path, temporary_directory):
    import duckdb
    connection = duckdb.connect(str(Path(path).resolve()), read_only=True,
        config={"memory_limit": "2GB", "threads": "2", "preserve_insertion_order": "false", "temp_directory": str(temporary_directory)})
    try:
        for table, required in REQUIRED_COLUMNS.items():
            actual = {row[0]: row[1] for row in connection.execute("DESCRIBE " + table).fetchall()}
            if any(actual.get(name) != kind for name, kind in required.items()):
                raise SourceError("Unexpected research schema: " + table)
    except BaseException:
        connection.close(); raise
    return connection
