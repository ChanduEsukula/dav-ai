"""Operator-managed, short-lived Render demo grants. No public activation API.

Trust: operator-controlled Render Secret Files + independently pinned signing-key
fingerprint. The offline private key is never present in the service. Revocation
is secret-file removal/replacement + maintenance/restart, NOT an external witness.
"""
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from app.security.publication_candidate import PublicSignaturePolicy, validate_signed_publication_claims
from app.security.trusted_state import LifecycleKey
from app.security.validation import AuthorizationRejected, parse_document, parse_timestamp

POLICY_FILE = Path('/etc/secrets/dav-ai-public-policy.json')
GRANT_FILE = Path('/etc/secrets/dav-ai-public-approval.json')
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
    # Fixed secret-file locations, no symlinks, writable-by-other files or unbounded reads.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_mode & 0o022:
            raise AuthorizationRejected('Unsafe operator document')
        raw = stream.read(16385)
        after = os.fstat(stream.fileno())
        current = path.lstat()
        identity = lambda x: (x.st_dev,x.st_ino,x.st_mode,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
        if identity(before) != identity(after) or identity(before) != identity(current):
            raise AuthorizationRejected('Operator document changed')
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
