from __future__ import annotations

import os
import sqlite3
from pathlib import Path


class PharmaceuticalReleaseUnavailable(RuntimeError):
    """Raised when the frozen pharmaceutical release cannot be opened safely."""


REQUIRED_TABLES = {
    "products",
    "ingredients",
    "product_ingredients",
    "product_identifiers",
    "search_names",
    "labels",
    "label_sections",
    "product_labels",
    "recalls",
    "product_recalls",
    "ae_summary",
    "ae_monthly",
    "ae_top_reactions",
    "safety_communications",
    "drug_communications",
    "coverage",
    "sources",
    "release_manifest",
}


def _repo_root() -> Path:
    # backend/app/db/pharma/release_connection.py
    return Path(__file__).resolve().parents[4]


def release_database_path() -> Path:
    configured = os.getenv("DAV_AI_PHARMA_RELEASE_DB")

    if configured:
        return Path(configured).expanduser().resolve()

    return (
        _repo_root()
        / "data"
        / "releases"
        / "dav_ai_pharma_v1"
        / "phase4b-communications-2026-10-06"
        / "pharma.sqlite"
    ).resolve()


def connect_release() -> sqlite3.Connection:
    path = release_database_path()

    if not path.is_file():
        raise PharmaceuticalReleaseUnavailable(
            f"Pharmaceutical release database not found: {path}"
        )

    try:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
            timeout=5.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA foreign_keys = ON")

        _validate_release(connection)

        return connection

    except sqlite3.Error as exc:
        raise PharmaceuticalReleaseUnavailable(
            f"Unable to open pharmaceutical release database: {path}"
        ) from exc


def _validate_release(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    available = {row["name"] for row in rows}
    missing = sorted(REQUIRED_TABLES - available)

    if missing:
        raise PharmaceuticalReleaseUnavailable(
            "Pharmaceutical release is missing required tables: "
            + ", ".join(missing)
        )

    manifest = connection.execute(
        """
        SELECT release_id, contract_id, policy_version, build_version
        FROM release_manifest
        LIMIT 2
        """
    ).fetchall()

    if len(manifest) != 1:
        raise PharmaceuticalReleaseUnavailable(
            "Pharmaceutical release must contain exactly one release manifest row"
        )

    row = manifest[0]

    if row["contract_id"] != "dav-ai-pharma-release-v1":
        raise PharmaceuticalReleaseUnavailable(
            f"Unexpected pharmaceutical release contract: {row['contract_id']}"
        )
