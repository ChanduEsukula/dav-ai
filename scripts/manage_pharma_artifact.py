"""Offline artifact-selection rehearsal. Never grants publication or edits a database.

Only operator CLI paths are accepted; this module is not an API or runtime dependency.
The deployed serving-denial guard intentionally remains in place.
Managed install/activate commands are separate from the legacy rehearsal commands.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.pharma.release_connection import artifact_signature, verify_artifact


@contextmanager
def registry_lock(root):
    root = Path(root)
    if root.is_symlink():
        raise ValueError("Registry must not be a symlink")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.stat().st_mode & 0o022:
        raise ValueError("Registry must not be writable by group/others")
    fd = os.open(root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield root


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        raw = stream.read(16385)
    if len(raw) > 16384:
        raise ValueError("Registry record exceeds size limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Invalid registry record")
    return value


def prepare(database, directory):
    path = Path(database).resolve(strict=True)
    if path.stat().st_mode & 0o222:
        raise ValueError("Use an immutable read-only release file")
    signature = artifact_signature(path)
    verified = verify_artifact(path)
    if artifact_signature(path) != signature:
        raise ValueError("Artifact changed during preparation")
    identity = hashlib.sha256((str(path) + verified["database_sha256"]).encode()).hexdigest()[:32]
    record = {"candidate_id": identity, "database": str(path), "signature": list(signature),
              "verification": verified, "prepared_at": datetime.now(timezone.utc).isoformat()}
    with registry_lock(directory) as root:
        destination = root / f"{identity}.json"
        if destination.exists():
            previous = read_json(destination)
            if any(previous.get(k) != record[k] for k in ("candidate_id", "database", "signature", "verification")):
                raise ValueError("Existing candidate differs; never overwrite it")
        else:
            atomic_json(destination, record)
    return identity


def candidate(root, identity):
    if not re.fullmatch(r"[0-9a-f]{32}", identity):
        raise ValueError("Invalid candidate identifier")
    record = read_json(root / f"{identity}.json")
    if record.get("candidate_id") != identity:
        raise ValueError("Candidate identity mismatch")
    path = Path(record["database"])
    if path.stat().st_mode & 0o222 or list(artifact_signature(path)) != record["signature"]:
        raise ValueError("Candidate file changed since preparation")
    # Rehash before every offline selection/rollback, never per request.
    if verify_artifact(path) != record["verification"]:
        raise ValueError("Candidate verification mismatch")
    if record["verification"].get("publication_validated") is not False:
        raise ValueError("This rehearsal cannot carry publication approval")
    return record


def select(directory, identity=None, rollback=False):
    with registry_lock(directory) as root:
        state = read_json(root / "active.json") if (root / "active.json").exists() else {}
        target = state.get("previous") if rollback else identity
        if not target:
            raise ValueError("No candidate selected for rollback")
        candidate(root, target)
        new = {"active": target, "previous": state.get("active"), "publication_authorized": False,
               "scope": "offline-rehearsal-only"}
        atomic_json(root / "active.json", new)
        return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--database", type=Path, required=True)
    build = commands.add_parser("prepare")
    build.add_argument("--database", type=Path, required=True)
    build.add_argument("--registry", type=Path, required=True)
    activate = commands.add_parser("select")
    activate.add_argument("--candidate", required=True)
    activate.add_argument("--registry", type=Path, required=True)
    back = commands.add_parser("rollback")
    back.add_argument("--registry", type=Path, required=True)
    for operation in ("install", "activate", "rollback-installed", "inspect", "discard-incomplete", "recover-selection"):
        command = commands.add_parser(operation)
        command.add_argument("--root", type=Path, required=True)
        if operation in {"install", "activate", "recover-selection"}:
            command.add_argument("--version", required=True)
        if operation == "install":
            command.add_argument("--source", type=Path, required=True)
        if operation == "discard-incomplete":
            command.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        from app.db.pharma import artifact_store as store
        if args.command == "install":
            result = store.install(args.source, args.root, args.version)
        elif args.command == "recover-selection":
            result = store.activate(args.root, args.version, recover=True)
        elif args.command == "activate":
            result = store.activate(args.root, args.version)
        elif args.command == "rollback-installed":
            result = store.activate(args.root, rollback=True)
        elif args.command == "inspect":
            result = store.inspect(args.root)
        elif args.command == "discard-incomplete":
            store.discard_incomplete(args.root, args.name)
            result = {"discarded": args.name, "publication_authorized": False}
        elif args.command == "verify":
            result = verify_artifact(args.database)
        elif args.command == "prepare":
            result = {"candidate_id": prepare(args.database, args.registry), "publication_authorized": False}
        else:
            result = select(args.registry, getattr(args, "candidate", None), args.command == "rollback")
        print(json.dumps(result, sort_keys=True, indent=2))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, sqlite3.Error) as exc:
        # Offline operator diagnostics never include report identifiers.
        print(f"Artifact operation refused: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
