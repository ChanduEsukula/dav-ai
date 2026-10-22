from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_DIR = (
    ROOT
    / "docs/evidence"
    / "pharma-release-v1-build-2026-10-06-phase4b-communications"
)

DATABASE = (
    ROOT
    / "data/releases/dav_ai_pharma_v1"
    / "phase4b-communications-2026-10-06/pharma.sqlite"
)

EXPECTED_RELEASE = (
    "dav-ai-pharma-v1-phase4b-communications-20261006"
)

EXPECTED_CONTRACT = "dav-ai-pharma-release-v1"
EXPECTED_POLICY = "1.0.0"
EXPECTED_SCHEMA_VERSION = 4


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(8 * 1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def verify() -> bool:
    errors = []

    try:
        metadata = json.loads(
            (EVIDENCE_DIR / "release_metadata.json").read_text()
        )
    except (OSError, ValueError) as exc:
        print(f"Metadata verification failed: {type(exc).__name__}")
        return False

    if not DATABASE.is_file():
        print("Database artifact is missing.")
        return False

    actual_size = DATABASE.stat().st_size
    expected_size = metadata.get("database_bytes")

    if actual_size != expected_size:
        errors.append("Database size mismatch")

    actual_digest = sha256_file(DATABASE)
    expected_digest = metadata.get("database_sha256")

    if actual_digest != expected_digest:
        errors.append("Database SHA-256 mismatch")

    if metadata.get("release_version") != EXPECTED_RELEASE:
        errors.append("Release metadata identity mismatch")

    try:
        connection = sqlite3.connect(
            f"{DATABASE.resolve().as_uri()}?mode=ro",
            uri=True,
        )

        try:
            connection.execute("PRAGMA query_only = ON")

            version = connection.execute(
                "PRAGMA user_version"
            ).fetchone()[0]

            if version != EXPECTED_SCHEMA_VERSION:
                errors.append("SQLite schema version mismatch")

            rows = connection.execute(
                "SELECT release_id, contract_id, policy_version "
                "FROM release_manifest LIMIT 2"
            ).fetchall()

            if len(rows) != 1:
                errors.append("Expected exactly one release manifest")
            else:
                release_id, contract_id, policy = rows[0]

                if release_id != EXPECTED_RELEASE:
                    errors.append("Release identity mismatch")

                if contract_id != EXPECTED_CONTRACT:
                    errors.append("Release contract mismatch")

                if policy != EXPECTED_POLICY:
                    errors.append("Release policy mismatch")
        finally:
            connection.close()

    except (sqlite3.Error, OSError) as exc:
        errors.append(
            f"SQLite verification failed: {type(exc).__name__}"
        )

    approved = metadata.get("publication_validated") is True

    print("Database size:", actual_size)
    print("SHA-256:", actual_digest)
    print("Publication approved:", approved)

    if not approved:
        print(
            "WARNING: Artifact is valid for local verification "
            "but not approved for public publication."
        )

    if errors:
        for error in errors:
            print("FAILED:", error)
        return False

    print("Artifact integrity verification: PASSED")
    return True


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
