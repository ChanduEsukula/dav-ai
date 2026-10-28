from __future__ import annotations

from contextlib import closing
import hashlib
import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from threading import Lock
import time
import stat

from app.db.database import is_deployed_environment


class PharmaceuticalReleaseUnavailable(RuntimeError):
    """Raised when the frozen pharmaceutical release cannot be opened safely."""


REQUIRED_TABLES = {
    "formulations",
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
    if "DAV_AI_PHARMA_ARTIFACT_ROOT" in os.environ:
        if not os.environ["DAV_AI_PHARMA_ARTIFACT_ROOT"].strip() or os.getenv("DAV_AI_PHARMA_RELEASE_DB"):
            raise PharmaceuticalReleaseUnavailable("Conflicting or empty managed artifact configuration")
        from app.db.pharma.artifact_store import pinned_path, regular
        path = pinned_path(os.environ["DAV_AI_PHARMA_ARTIFACT_ROOT"])
        regular(path, immutable=True)
        return path
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
    """
    Open the frozen pharmaceutical release in read-only mode.

    Local development is permitted.

    Deployed environments require an operator-signed, short-lived demonstration
    grant in addition to the original pinned artifact and immutable read checks.
    """

    deployed = is_deployed_environment()
    if deployed:
        from app.security.production_authorization import require_production_authorization
        try:
            require_production_authorization()
        except Exception:
            raise PharmaceuticalReleaseUnavailable("Pharmaceutical release is not authorized for deployed environments") from None

    connection = None

    try:
        path = release_database_path()
        if deployed:
            mode = path.lstat().st_mode
            if not stat.S_ISREG(mode) or mode & 0o222:
                raise PharmaceuticalReleaseUnavailable("Production artifact must be an immutable regular file")
        signature = artifact_signature(path)
        if signature[2] != EXPECTED_BYTES:
            raise PharmaceuticalReleaseUnavailable("Unexpected pharmaceutical artifact size")
        # Serialize cold verification; concurrent cache misses must not each hash 4.83 GB.
        with _verification_lock:
            _verify_checksum(str(path), signature[2], signature[3], signature[4], signature[0], signature[1])
        connection = sqlite3.connect(
            f"{path.as_uri()}?mode=ro&immutable=1",
            uri=True,
            timeout=5.0,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA foreign_keys = ON")

        if deployed:
            from app.services.public_evidence import QUERY_DEADLINE
            deadline = min(QUERY_DEADLINE.get() or time.monotonic() + 10, time.monotonic() + 8)
            connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)

        _validate_release(connection)
        if artifact_signature(path) != signature:
            raise PharmaceuticalReleaseUnavailable("Pharmaceutical artifact replaced while opening")

        if deployed:
            require_production_authorization()

        return connection

    except (sqlite3.Error, PharmaceuticalReleaseUnavailable, OSError, ValueError, KeyError, TypeError) as exc:
        if connection is not None:
            connection.close()

        raise PharmaceuticalReleaseUnavailable(
            "Unable to open or validate pharmaceutical release"
        ) from exc


def _validate_release(connection: sqlite3.Connection) -> None:
    """
    Validate the required pharmaceutical release
    tables and manifest contract.
    """

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
            "Pharmaceutical release must contain exactly "
            "one release manifest row"
        )

    row = manifest[0]
    if (connection.execute("PRAGMA user_version").fetchone()[0] != 4
            or row["release_id"] != "dav-ai-pharma-v1-phase4b-communications-20261006"
            or row["policy_version"] != "1.0.0"):
        raise PharmaceuticalReleaseUnavailable("Incompatible pharmaceutical release version or policy")

    if row["contract_id"] != "dav-ai-pharma-release-v1":
        raise PharmaceuticalReleaseUnavailable(
            "Unexpected pharmaceutical release contract: "
            f"{row['contract_id']}"
        )


EXPECTED_BYTES = 4_825_108_480
_verification_lock = Lock()

EXPECTED_SHA256 = "87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71"


@lru_cache(maxsize=4)
def _verify_checksum(path: str, size: int, mtime_ns: int, ctime_ns: int, device=None, inode=None) -> None:
    """Cache integrity by file identity; integrity never grants publication approval."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    current = Path(path).stat()
    if device is not None and (current.st_dev, current.st_ino) != (device, inode):
        raise PharmaceuticalReleaseUnavailable("Pharmaceutical artifact replaced during verification")
    if (current.st_size, current.st_mtime_ns, current.st_ctime_ns) != (size, mtime_ns, ctime_ns):
        raise PharmaceuticalReleaseUnavailable("Pharmaceutical artifact changed during verification")
    if digest.hexdigest() != EXPECTED_SHA256:
        raise PharmaceuticalReleaseUnavailable("Pharmaceutical artifact checksum does not match the frozen release")


def artifact_signature(path: Path):
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(path) + suffix)
        if sidecar.exists() or sidecar.is_symlink():
            raise PharmaceuticalReleaseUnavailable("Frozen artifacts must not have SQLite sidecars")
    stat = path.stat()
    if not path.is_file():
        raise PharmaceuticalReleaseUnavailable("Pharmaceutical artifact is not a regular file")
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def verify_artifact(path: Path):
    """Offline activation/install check. Always hash; no publication authorization implied."""
    path = path.resolve(strict=True)
    signature = artifact_signature(path)
    if signature[2] != EXPECTED_BYTES:
        raise PharmaceuticalReleaseUnavailable("Unexpected pharmaceutical artifact size")
    # Explicit offline verification bypasses the runtime checksum cache.
    _verify_checksum.__wrapped__(str(path), signature[2], signature[3], signature[4], signature[0], signature[1])
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro&immutable=1", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        _validate_release(con)
    if artifact_signature(path) != signature:
        raise PharmaceuticalReleaseUnavailable("Artifact replaced during verification")
    return {"release_id": "dav-ai-pharma-v1-phase4b-communications-20261006",
            "database_bytes": EXPECTED_BYTES, "database_sha256": EXPECTED_SHA256,
            "schema_user_version": 4, "publication_validated": False}
