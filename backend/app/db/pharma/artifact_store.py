"""Provider-neutral immutable installations; selection is never publication approval.

Only the operator CLI writes here. The application mounts the store read-only.
Filesystem ownership is a trust boundary; no untrusted process may write the root.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid

FORMAT = "dav-ai-installed-release-v1"
STATE_FORMAT = "dav-ai-activation-v1"
VERSION = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")


def version_id(value):
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError("Invalid installation version")
    return value


def checked_root(root, *, create=False):
    root = Path(root).absolute()
    # Reject a symlink root. Ancestors are canonicalized (including macOS /tmp).
    # Canonical ancestors must be operator-controlled; see OPERATIONS.md.
    if root.is_symlink():
        raise ValueError("Artifact root must not be a symlink")
    root = root.resolve(strict=not create)
    if create:
        root.mkdir(mode=0o755, parents=True, exist_ok=True)
    info = root.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o022:
        raise ValueError("Artifact root must be an operator-controlled directory")
    return root


def regular(path, *, immutable=False):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
        raise ValueError("Expected operator-controlled regular file")
    if immutable and info.st_mode & 0o222:
        raise ValueError("Installed artifacts must be read-only")
    return info


def directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o022:
        raise ValueError("Expected operator-controlled directory")


def read_json(path):
    def identity(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
                info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    before = regular(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor) as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_mode & 0o022
                or (opened.st_dev, opened.st_ino, opened.st_ctime_ns)
                != (before.st_dev, before.st_ino, before.st_ctime_ns)):
            raise ValueError("Artifact record changed while opening")
        data = stream.read(16385)
        if (identity(os.fstat(stream.fileno())) != identity(opened)
                or identity(path.lstat()) != identity(opened)):
            raise ValueError("Artifact record changed while reading")
    if len(data) > 16384:
        raise ValueError("Artifact record too large")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Invalid artifact record")
    return value


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value, *, mode=0o644):
    fd, pending = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(pending, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)


@contextmanager
def writer(root):
    root = checked_root(root, create=True)
    # Files may be readable by the unprivileged runtime, writable only by operator.
    if root.stat().st_uid not in {os.geteuid(), 0} and os.geteuid() != 0:
        raise PermissionError("Artifact root is owned by another operator")
    fd = os.open(root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, "w") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_nlink != 1
                or info.st_uid != os.geteuid()):
            raise PermissionError("Unsafe artifact writer lock")
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield root


def expected_verification():
    from app.db.pharma.release_connection import EXPECTED_BYTES, EXPECTED_SHA256
    return {"release_id": "dav-ai-pharma-v1-phase4b-communications-20261006",
            "database_bytes": EXPECTED_BYTES, "database_sha256": EXPECTED_SHA256,
            "schema_user_version": 4, "publication_validated": False}


def verify(path):
    from app.db.pharma.release_connection import verify_artifact
    return verify_artifact(path)


def installed(root, version, *, reverify=False):
    version_id(version)
    root = checked_root(root)
    directory(root / "releases")
    release = root / "releases" / version
    directory(release)
    receipt = read_json(release / "receipt.json")
    if (receipt.get("format") != FORMAT or receipt.get("version") != version
            or receipt.get("verification") != expected_verification()):
        raise ValueError("Installed release receipt is incompatible")
    path = release / "pharma.sqlite"
    info = regular(path, immutable=True)
    if info.st_size != expected_verification()["database_bytes"]:
        raise ValueError("Installed artifact size mismatch")
    if reverify and verify(path) != receipt["verification"]:
        raise ValueError("Installed artifact verification mismatch")
    return path


def state(root):
    value = read_json(root / "activation.json")
    if (value.get("format") != STATE_FORMAT or value.get("publication_authorized") is not False
            or not re.fullmatch(r"[0-9a-f]{32}", str(value.get("generation", "")))):
        raise ValueError("Invalid activation state")
    version_id(value.get("active"))
    if value.get("previous") is not None:
        version_id(value["previous"])
    return value


def install(source, root, version):
    """Stream a new managed copy; never change source, overwrite a version, or activate."""
    from app.db.pharma.release_connection import artifact_signature
    version_id(version)
    source = Path(source).resolve(strict=True)
    signature = artifact_signature(source)
    expected = expected_verification()
    if signature[2] != expected["database_bytes"]:
        raise ValueError("Source artifact size mismatch")
    with writer(root) as root:
        releases = root / "releases"
        releases.mkdir(mode=0o755, exist_ok=True)
        directory(releases)
        destination = releases / version
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("Installation versions are never overwritten")
        pending = Path(tempfile.mkdtemp(prefix=".install-", dir=releases))
        try:
            digest = hashlib.sha256()
            copied = pending / "pharma.sqlite"
            # Source is read-only even if its external mode allows writes.
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
            copied_bytes = 0
            with os.fdopen(fd, "rb") as src, copied.open("xb") as dst:
                for chunk in iter(lambda: src.read(8 * 1024 * 1024), b""):
                    copied_bytes += len(chunk)
                    if copied_bytes > expected["database_bytes"]:
                        raise ValueError("Source grew during installation")
                    digest.update(chunk)
                    dst.write(chunk)
                dst.flush()
                os.fchmod(dst.fileno(), 0o444)
                os.fsync(dst.fileno())
            if artifact_signature(source) != signature or digest.hexdigest() != expected["database_sha256"]:
                raise ValueError("Source changed or checksum mismatch during installation")
            verification = verify(copied)  # Always rehash copied bytes, plus exact schema/tables/identity.
            if verification != expected:
                raise ValueError("Incompatible copied artifact")
            atomic_json(pending / "receipt.json", {
                "format": FORMAT, "version": version, "verification": verification,
                "installed_at": datetime.now(timezone.utc).isoformat(),
            }, mode=0o444)
            sync_directory(pending)
            os.chmod(pending, 0o555)
            os.rename(pending, destination)
            sync_directory(releases)
            return {"version": version, "verification": verification, "activated": False}
        finally:
            if pending.exists():
                os.chmod(pending, 0o700)
                shutil.rmtree(pending)  # Only this operation's newly-created incomplete directory.


def activate(root, version=None, *, rollback=False, recover=False):
    with writer(root) as root:
        selection_exists = (root / "activation.json").exists() or (root / "activation.json").is_symlink()
        try:
            previous = state(root) if selection_exists else None
        except (OSError, ValueError, KeyError, TypeError):
            if not recover:
                raise
            previous = None
        else:
            if recover and previous is not None:
                raise ValueError("Healthy selection must use normal activation")
        target = previous.get("previous") if rollback and previous else version
        if target is None:
            raise ValueError("No rollback target; explicitly activate a retained version")
        installed(root, target, reverify=True)
        if previous and previous["active"] == target:
            return previous  # Idempotent activation must not destroy the rollback target.
        value = {"format": STATE_FORMAT, "active": target,
                 "previous": previous["active"] if previous else None,
                 "generation": uuid.uuid4().hex, "publication_authorized": False}
        atomic_json(root / "activation.json", value)
        return value


def inspect(root):
    root = checked_root(root)
    releases = root / "releases"
    directory(releases)
    activation = None
    activation_error = None
    try:
        activation = state(root)
    except FileNotFoundError:
        activation_error = "missing"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        activation_error = type(exc).__name__
    return {"activation": activation, "activation_error": activation_error,
            "installed": sorted(p.name for p in releases.iterdir() if VERSION.fullmatch(p.name)),
            "incomplete": sorted(p.name for p in releases.iterdir() if p.name.startswith(".install-")),
            "publication_authorized": False}


def discard_incomplete(root, name):
    if not re.fullmatch(r"\.install-[a-z0-9_]{8}", name):
        raise ValueError("Invalid incomplete-install identifier")
    with writer(root) as root:
        releases = root / "releases"
        directory(releases)
        pending = releases / name
        directory(pending)
        # Crash recovery only removes known installer-owned files, never arbitrary directories.
        if {p.name for p in pending.iterdir()} - {"pharma.sqlite", "receipt.json"}:
            raise ValueError("Unknown files in incomplete installation; manual review required")
        for path in pending.iterdir():
            regular(path, immutable=False)
        os.chmod(pending, 0o700)
        for path in pending.iterdir():
            path.unlink()
        pending.rmdir()
        sync_directory(releases)


@lru_cache(maxsize=4)
def pinned_path(root):
    """Pin a verified-format immutable selection for process lifetime. Restart to cut over."""
    root = checked_root(root)
    selected = state(root)
    return installed(root, selected["active"])
