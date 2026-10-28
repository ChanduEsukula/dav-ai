"""Offline PUBLIC approval candidate validation. NEVER imported by the serving API.

A positive result is not a serving capability. Policy and rollback-resistant
state must be independently provisioned; there is no environment/file loader,
activation endpoint, live trust root or exception to deployed-mode denial here.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import re

from cryptography.exceptions import InvalidSignature
from app.security.trusted_state import TrustPolicy, StateStore, _read, _record
from app.security.validation import AuthorizationRejected, check_signature_input, parse_document, parse_timestamp, utc_time

PURPOSE = 'dav-ai-public-evidence-v1'
OPERATIONS = (
    'GET /api/drugs/search', 'GET /api/drugs/{product_id}',
    'GET /api/drugs/{product_id}/safety', 'GET /api/drugs/{product_id}/timeline',
    'GET /api/drugs/{product_id}/safety/{section}', 'GET /api/coverage',
    'GET /api/drugs/{product_id}/evidence', 'GET /api/medications/overview',
    'GET /api/coverage/inventory', 'POST /api/v1/reports/pharmaceutical',
)
FIELDS = frozenset({'purpose', 'approval_id', 'key_id', 'release_id', 'database_sha256',
    'deployment_id', 'application_sha256', 'review_bundle_sha256', 'environment',
    'audience', 'operations', 'issued_at', 'expires_at'})


@dataclass(frozen=True)
class PublicCandidatePolicy:
    trust: TrustPolicy
    application_sha256: str
    review_bundle_sha256: str

    def __post_init__(self):
        if not isinstance(self.trust, TrustPolicy):
            raise ValueError('Independent trust policy required')
        if any(type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value)
               for value in (self.application_sha256, self.review_bundle_sha256)):
            raise ValueError('Exact application and review bundle digests required')


def validate_publication_candidate(*, payload: bytes, signature: bytes,
                                   policy: PublicCandidatePolicy, store: StateStore,
                                   now: datetime | None = None) -> dict:
    """Authenticate a review-bound candidate with existing revocation safeguards.

    This does not validate the substantive review or establish who provisioned
    policy/store. Every caller is an offline reviewer, never a public request.
    """
    if not isinstance(policy, PublicCandidatePolicy):
        raise AuthorizationRejected('Trusted public policy required')
    current = utc_time(now if now is not None else datetime.now(timezone.utc))
    trust = policy.trust
    checkpoint = _read(store, trust)
    record = _record(checkpoint.payload, checkpoint.signature, trust, checkpoint.sequence_number, current)
    if (record['sequence_number'] != checkpoint.sequence_number
            or frozenset(record['revoked_approval_ids']) != checkpoint.revoked_approval_ids
            or frozenset(record['revoked_signing_key_ids']) != checkpoint.revoked_signing_key_ids):
        raise AuthorizationRejected('Trusted state inconsistent')
    claims = parse_document(payload, limit=8192, label='public approval', duplicate='Duplicate public approval field')
    if set(claims) != FIELDS:
        raise AuthorizationRejected('Unexpected public approval claims')
    if any(type(value) is not str or not value for key, value in claims.items() if key != 'operations'):
        raise AuthorizationRejected('Public approval claims must be nonempty strings')
    check_signature_input(signature)
    key = trust.approval_keys.get(claims['key_id'])
    if key is None:
        raise AuthorizationRejected('Untrusted public signing key')
    try:
        key.public_key.verify(signature, payload)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise AuthorizationRejected('Invalid public approval signature') from exc
    expected = {'purpose': PURPOSE, 'release_id': trust.release_id,
                'database_sha256': trust.database_sha256, 'deployment_id': trust.deployment_id,
                'application_sha256': policy.application_sha256,
                'review_bundle_sha256': policy.review_bundle_sha256,
                'environment': 'production', 'audience': 'public'}
    if any(claims[field] != value for field, value in expected.items()):
        raise AuthorizationRejected('Public approval scope mismatch')
    if claims['operations'] != list(OPERATIONS):
        raise AuthorizationRejected('Unapproved public operation scope')
    issued, expires = parse_timestamp(claims['issued_at']), parse_timestamp(claims['expires_at'])
    if not issued <= current < expires or expires <= issued or expires - issued > timedelta(hours=24):
        raise AuthorizationRejected('Invalid public approval validity window')
    key.check(issued, expires, current)
    if (claims['approval_id'] in checkpoint.revoked_approval_ids
            or claims['key_id'] in checkpoint.revoked_signing_key_ids):
        raise AuthorizationRejected('Public approval or signer revoked')
    if _read(store, trust) != checkpoint:
        raise AuthorizationRejected('Trusted state changed during public decision')
    return {'approval_id': claims['approval_id'], 'approval_payload_sha256': hashlib.sha256(payload).hexdigest(),
            'review_bundle_sha256': policy.review_bundle_sha256,
            'candidate_verified': True, 'publication_authorized': False}
