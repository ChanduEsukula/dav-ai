"""Operator-managed, short-lived Render demo grants. No public activation API.

Trust: operator-controlled Render Secret Files + independently pinned signing-key
fingerprint. The offline private key is never present in the service. Revocation
is secret-file removal/replacement + maintenance/restart, NOT an external witness.
"""
import base64
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from app.security.publication_candidate import PublicSignaturePolicy, validate_signed_publication_claims
from app.security.trusted_state import LifecycleKey
from app.security.validation import AuthorizationRejected, parse_document, parse_timestamp

POLICY_FILE = Path('/etc/secrets/dav-ai-public-policy.json')
GRANT_FILE = Path('/etc/secrets/dav-ai-public-approval.json')
RENDER_SECRET_ROOT = Path('/etc/secrets')
RELEASE_ID = 'dav-ai-pharma-v1-phase4b-communications-20261006'
# Deliberately no PDF, communications, timeline, aggregate safety or research authority.
READ_OPERATIONS = (
    'GET /api/drugs/search', 'GET /api/drugs/{product_id}',
    'GET /api/drugs/{product_id}/evidence', 'GET /api/drugs/{product_id}/safety/labels',
    'GET /api/drugs/{product_id}/safety/recalls', 'GET /api/drugs/{product_id}/safety/adverse_events',
    'GET /api/medications/overview', 'GET /api/coverage', 'GET /api/coverage/inventory',
)
POLICY_FIELDS = {'key_id','public_key_base64','deployment_id','review_bundle_sha256','not_before','not_after'}


@lru_cache(maxsize=1)
def application_digest():
    root = Path(__file__).resolve().parents[1]
    manifest = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(root.rglob('*.py')) if '__pycache__' not in p.parts}
    return hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def operator_document(path):
    """Read a fixed document or Render's exact projected Secret File layout.

    Only filename -> ..data/filename and optional ..data -> ..generation are
    followed. Each real directory/file is opened relative to a pinned directory
    descriptor with NOFOLLOW; links, canonical paths and identities must remain
    unchanged through the bounded read. Symlink mode bits are not file access
    permissions. Only Render's root-owned sticky parent may be writable: all
    protected entries must then be root-owned, so non-root callers cannot rename
    them. Generation directories and files must remain non-group/world-writable.
    """
    path = Path(path)
    identity = lambda x: (x.st_dev,x.st_ino,x.st_mode,x.st_uid,x.st_gid,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        if not path.is_absolute() or '..' in path.parts:
            raise AuthorizationRejected('Invalid operator document path')
        root = path.parent
        root_before = root.lstat()
        sticky_root = (root == RENDER_SECRET_ROOT and root_before.st_uid == 0
                       and bool(root_before.st_mode & stat.S_ISVTX)
                       and path.name in {'dav-ai-public-policy.json','dav-ai-public-approval.json'})
        if not stat.S_ISDIR(root_before.st_mode) or (root_before.st_mode & 0o022 and not sticky_root):
            raise AuthorizationRejected('Unsafe operator directory')
        canonical_root = root.resolve(strict=True)
        with ExitStack() as stack:
            def open_directory(name, parent=None):
                fd = os.open(name,directory_flags,dir_fd=parent)
                stack.callback(os.close,fd)
                info = os.fstat(fd)
                is_sticky_parent = parent is None and sticky_root and info.st_uid == 0 and info.st_mode & stat.S_ISVTX
                if (not stat.S_ISDIR(info.st_mode)
                        or (info.st_mode & 0o022 and not is_sticky_parent)
                        or (sticky_root and info.st_uid != 0)):
                    raise AuthorizationRejected('Unsafe operator directory')
                return fd, info

            root_fd, opened_root = open_directory(canonical_root)
            if identity(root_before) != identity(opened_root):
                raise AuthorizationRejected('Operator directory changed')
            directories = [(root_fd,canonical_root,opened_root)]
            links = []
            leaf = os.stat(path.name,dir_fd=root_fd,follow_symlinks=False)
            if sticky_root and leaf.st_uid != 0:
                raise AuthorizationRejected('Untrusted operator entry owner')
            parent_fd, canonical_parent = root_fd, canonical_root
            if stat.S_ISLNK(leaf.st_mode):
                if path.name not in {'dav-ai-public-policy.json','dav-ai-public-approval.json'}:
                    raise AuthorizationRejected('Unexpected operator symlink')
                target = os.readlink(path.name,dir_fd=root_fd)
                if target != '..data/'+path.name:
                    raise AuthorizationRejected('Unexpected operator symlink target')
                links.append((path.name,leaf,target))
                data_info = os.stat('..data',dir_fd=root_fd,follow_symlinks=False)
                if sticky_root and data_info.st_uid != 0:
                    raise AuthorizationRejected('Untrusted operator generation owner')
                generation = '..data'
                if stat.S_ISLNK(data_info.st_mode):
                    generation = os.readlink('..data',dir_fd=root_fd)
                    if not re.fullmatch(r'\.\.[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',generation) or generation == '..data':
                        raise AuthorizationRejected('Unexpected operator generation target')
                    links.append(('..data',data_info,generation))
                elif not stat.S_ISDIR(data_info.st_mode):
                    raise AuthorizationRejected('Unsafe operator generation')
                parent_fd, opened_parent = open_directory(generation,root_fd)
                canonical_parent = canonical_root/generation
                directories.append((parent_fd,canonical_parent,opened_parent))

            before = os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False)
            if (not stat.S_ISREG(before.st_mode) or before.st_mode & 0o022
                    or (sticky_root and before.st_uid != 0)):
                raise AuthorizationRejected('Unsafe operator document')
            fd = os.open(path.name,file_flags,dir_fd=parent_fd)
            stream = stack.enter_context(os.fdopen(fd,'rb'))
            if identity(before) != identity(os.fstat(stream.fileno())):
                raise AuthorizationRejected('Operator document changed while opening')
            raw = stream.read(16385)
            if (identity(before) != identity(os.fstat(stream.fileno()))
                    or identity(before) != identity(os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False))):
                raise AuthorizationRejected('Operator document changed')
            for name, info, target in links:
                if (identity(info) != identity(os.stat(name,dir_fd=root_fd,follow_symlinks=False))
                        or os.readlink(name,dir_fd=root_fd) != target):
                    raise AuthorizationRejected('Operator symlink changed')
            for directory_fd, canonical, info in directories:
                if (identity(info) != identity(os.fstat(directory_fd))
                        or identity(info) != identity(canonical.lstat())):
                    raise AuthorizationRejected('Operator directory changed')
            if (root.resolve(strict=True) != canonical_root
                    or identity(root.lstat()) != identity(opened_root)
                    or path.resolve(strict=True) != canonical_parent/path.name):
                raise AuthorizationRejected('Operator canonical path changed')
    except (OSError, RuntimeError) as exc:
        raise AuthorizationRejected('Unsafe or changing operator document') from exc
    return parse_document(raw,limit=16384,label='operator document',duplicate='Duplicate operator field')


def decode(value):
    if type(value) is not str: raise AuthorizationRejected('Invalid encoded approval')
    try: return base64.b64decode(value,validate=True)
    except (ValueError,TypeError) as exc: raise AuthorizationRejected('Invalid encoded approval') from exc


@dataclass(frozen=True)
class Grant:
    approval_id: str
    payload_sha256: str
    expires_at: datetime


def require_production_authorization(now=None):
    """Fresh check at startup, each connection/request and before response release."""
    from app.db.pharma.release_connection import EXPECTED_SHA256
    try:
        if os.getenv('DAVAI_ENV','').lower() != 'production' or os.getenv('RENDER','').lower() != 'true':
            raise AuthorizationRejected('Only explicit Render production supported')
        if any(name in os.environ and os.environ[name].lower() not in {'prod','production'}
               for name in ('APP_ENV','ENVIRONMENT','PYTHON_ENV')):
            raise AuthorizationRejected('Conflicting deployment environment')
        trusted = operator_document(POLICY_FILE)
        if set(trusted) != POLICY_FIELDS: raise AuthorizationRejected('Invalid operator policy')
        public_bytes = decode(trusted['public_key_base64'])
        fingerprint = hashlib.sha256(public_bytes).hexdigest()
        if fingerprint != os.getenv('DAV_AI_PUBLIC_KEY_SHA256'):
            raise AuthorizationRejected('Unpinned operator signing key')
        if not os.getenv('RENDER_SERVICE_ID') or trusted['deployment_id'] != os.environ['RENDER_SERVICE_ID']:
            raise AuthorizationRejected('Wrong Render service')
        policy = PublicSignaturePolicy(RELEASE_ID,EXPECTED_SHA256,trusted['deployment_id'],application_digest(),
            trusted['review_bundle_sha256'],{trusted['key_id']:LifecycleKey(Ed25519PublicKey.from_public_bytes(public_bytes),
                parse_timestamp(trusted['not_before']),parse_timestamp(trusted['not_after']))})
        envelope = operator_document(GRANT_FILE)
        if set(envelope) != {'payload_base64','signature_base64'}:
            raise AuthorizationRejected('Invalid operator grant')
        payload, signature = decode(envelope['payload_base64']),decode(envelope['signature_base64'])
        claims = validate_signed_publication_claims(payload=payload,signature=signature,policy=policy,
            now=now or datetime.now(timezone.utc),operations=READ_OPERATIONS)
        return Grant(claims['approval_id'],hashlib.sha256(payload).hexdigest(),parse_timestamp(claims['expires_at']))
    except Exception as exc:
        # Fail closed even for malformed JSON/types, unavailable files or key material.
        raise AuthorizationRejected('Public evidence serving is not authorized') from exc


if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['digest']: raise SystemExit('Usage: python -m app.security.production_authorization digest')
    print(application_digest())
