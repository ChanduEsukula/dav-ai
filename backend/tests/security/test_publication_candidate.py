"""Synthetic offline approvals only: no production trust anchor or live activation."""
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.security.publication_candidate import PublicCandidatePolicy, PURPOSE, OPERATIONS, validate_publication_candidate
from app.security.trusted_state import LifecycleKey, TrustPolicy, RevocationCheckpoint, accept_signed_revocation
from app.security.validation import AuthorizationRejected

NOW = datetime(2026, 10, 27, 20, tzinfo=timezone.utc)

class OfflineStore:
    """Process-local test fake, never a qualified durable production store."""
    def __init__(self):
        self.checkpoint = RevocationCheckpoint('test-authority', 0)
    def read(self, authority):
        return self.checkpoint
    def compare_and_swap(self, authority, previous, replacement):
        if previous != self.checkpoint:
            return False
        self.checkpoint = replacement
        return True

@pytest.fixture
def case():
    approval, revocation = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    lifecycle = lambda key: LifecycleKey(key.public_key(), NOW-timedelta(days=1), NOW+timedelta(days=2))
    policy = PublicCandidatePolicy(TrustPolicy('test-authority', 'test-release', 'a'*64, 'test-deployment',
                                   {'test-maintainer':lifecycle(approval)}, {'test-revoker':lifecycle(revocation)}), 'b'*64, 'c'*64)
    store = OfflineStore()
    record = {'schema_version':'1','authority_id':'test-authority','key_id':'test-revoker','sequence_number':1,
              'issued_at':NOW.isoformat(),'expires_at':(NOW+timedelta(minutes=4)).isoformat(),
              'revoked_approval_ids':[],'revoked_signing_key_ids':[]}
    raw = json.dumps(record).encode()
    accept_signed_revocation(payload=raw, signature=revocation.sign(raw), policy=policy.trust, store=store, now=NOW)
    claims = {'purpose':PURPOSE,'approval_id':'test-review-only','key_id':'test-maintainer',
              'release_id':'test-release','database_sha256':'a'*64,'deployment_id':'test-deployment',
              'application_sha256':'b'*64,'review_bundle_sha256':'c'*64,'environment':'production','audience':'public',
              'operations':list(OPERATIONS),'issued_at':NOW.isoformat(),'expires_at':(NOW+timedelta(hours=1)).isoformat()}
    return policy, store, approval, revocation, claims


def decide(case, *, claims=None, signature=None, now=NOW):
    policy, store, signer, _, original = case
    raw = json.dumps(original if claims is None else claims).encode()
    return validate_publication_candidate(payload=raw, signature=signer.sign(raw) if signature is None else signature,
                                           policy=policy, store=store, now=now)


def test_authentic_review_candidate_is_not_public_serving_authorization(case):
    result = decide(case)
    assert result['candidate_verified'] is True and result['publication_authorized'] is False
    assert len(result['approval_payload_sha256']) == 64

@pytest.mark.parametrize('field,value', [('purpose','private-staging'),('environment','staging'),('audience','private'),
    ('release_id','foreign'),('database_sha256','d'*64),('deployment_id','cloned'),
    ('application_sha256','e'*64),('review_bundle_sha256','f'*64),('key_id','self-signed'),
    ('operations',list(OPERATIONS)+['POST /api/local/research/sessions']),('operations',list(OPERATIONS[:-1])),
    ('expires_at',(NOW+timedelta(days=366)).isoformat()),('issued_at',(NOW+timedelta(seconds=1)).isoformat())])
def test_even_signed_wrong_scope_or_excess_authority_denies(case, field, value):
    with pytest.raises(AuthorizationRejected):
        decide(case, claims={**case[4],field:value})

@pytest.mark.parametrize('signature',[b'',b'x'*64])
def test_bad_signatures_deny(case,signature):
    with pytest.raises(AuthorizationRejected):
        decide(case,signature=signature)


def test_forged_signer_cannot_self_authorize(case):
    raw=json.dumps(case[4]).encode()
    with pytest.raises(AuthorizationRejected):
        decide(case,signature=Ed25519PrivateKey.generate().sign(raw))


def test_duplicate_and_extra_claims_deny(case):
    raw=json.dumps(case[4]).encode()
    raw=raw[:-1]+b',"audience":"public"}'
    with pytest.raises(AuthorizationRejected):
        validate_publication_candidate(payload=raw,signature=case[2].sign(raw),policy=case[0],store=case[1],now=NOW)
    with pytest.raises(AuthorizationRejected):
        decide(case,claims={**case[4],'publication_validated':True})


def test_expired_revocation_denies_even_when_approval_is_current(case):
    with pytest.raises(AuthorizationRejected):
        decide(case,now=NOW+timedelta(minutes=5))

@pytest.mark.parametrize('field,value',[('revoked_approval_ids',['test-review-only']),('revoked_signing_key_ids',['test-maintainer'])])
def test_revoked_approval_or_signer_denies(case,field,value):
    checkpoint=case[1].checkpoint
    record=json.loads(checkpoint.payload)
    record.update(sequence_number=2,**{field:value})
    raw=json.dumps(record).encode()
    accept_signed_revocation(payload=raw,signature=case[3].sign(raw),policy=case[0].trust,store=case[1],now=NOW)
    with pytest.raises(AuthorizationRejected):
        decide(case)


def test_missing_unavailable_or_changed_trusted_state_denies(case,monkeypatch):
    original=case[1].read
    monkeypatch.setattr(case[1],'read',lambda _:None)
    with pytest.raises(AuthorizationRejected): decide(case)
    def failed(_): raise OSError('test unavailable')
    monkeypatch.setattr(case[1],'read',failed)
    with pytest.raises(AuthorizationRejected): decide(case)
    calls=[]
    def changed(authority):
        calls.append(1)
        return original(authority) if len(calls)==1 else replace(original(authority),sequence_number=2)
    monkeypatch.setattr(case[1],'read',changed)
    with pytest.raises(AuthorizationRejected): decide(case)

@pytest.mark.parametrize('environment',['production','staging','preview'])
def test_valid_offline_candidate_and_environment_flags_never_enable_runtime(case,monkeypatch,environment):
    assert decide(case)['candidate_verified']
    from app.db.pharma.release_connection import connect_release, PharmaceuticalReleaseUnavailable
    monkeypatch.setenv('DAVAI_ENV',environment)
    monkeypatch.setenv('PUBLICATION_VALIDATED','true')
    monkeypatch.setenv('DAV_AI_PUBLICATION_APPROVED','true')
    with pytest.raises(PharmaceuticalReleaseUnavailable,match='not authorized'):
        connect_release()
