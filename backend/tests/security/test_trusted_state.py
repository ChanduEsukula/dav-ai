"""Synthetic keys and a process-local contract fake; no production state provider."""

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security.trusted_state import (
    LifecycleKey, RevocationCheckpoint, TrustPolicy, accept_signed_revocation,
    validate_trusted_staging_decision,
)
from app.security.staging_authorization import AuthorizationRejected

NOW = datetime(2026, 10, 22, 15, tzinfo=timezone.utc)


class ContractStore:
    """Test-only CAS fake. Separate witness simulates an external rollback check.

    Neither field is persistent or independently trusted in this fake.
    """
    def __init__(self):
        self.value = RevocationCheckpoint("authority", 0)
        self.witness = 0
        self.lock = Lock()

    def read(self, authority):
        with self.lock:
            if self.value is not None and self.value.sequence_number < self.witness:
                raise OSError("rollback detected by simulated external witness")
            return self.value

    def compare_and_swap(self, authority, expected, replacement):
        with self.lock:
            if self.value != expected:
                return False
            self.value = replacement
            self.witness = replacement.sequence_number
            return True


@pytest.fixture
def case():
    approval_key, revocation_key = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    def life(key):
        return LifecycleKey(key.public_key(), NOW - timedelta(hours=2), NOW + timedelta(hours=2))
    policy = TrustPolicy("authority", "release", "a" * 64, "deployment",
                         {"approval": life(approval_key)}, {"revocation": life(revocation_key)})
    approval = dict(approval_id="id", key_id="approval", release_id="release", database_sha256="a" * 64,
                    environment="staging", audience="private", deployment_id="deployment",
                    issued_at=(NOW - timedelta(minutes=1)).isoformat(),
                    expires_at=(NOW + timedelta(minutes=30)).isoformat())
    record = dict(schema_version="1", authority_id="authority", key_id="revocation", sequence_number=1,
                  issued_at=(NOW - timedelta(minutes=1)).isoformat(),
                  expires_at=(NOW + timedelta(minutes=3)).isoformat(),
                  revoked_approval_ids=[], revoked_signing_key_ids=[])
    return policy, ContractStore(), approval_key, revocation_key, approval, record


def signed(document, key):
    payload = json.dumps(document).encode()
    return payload, key.sign(payload)


def ingest(case, **overrides):
    policy, store, _, key, _, record = case
    payload, signature = signed(record, key)
    args = dict(payload=payload, signature=signature, policy=policy, store=store, now=NOW)
    args.update(overrides)
    return accept_signed_revocation(**args)


def decide(case, **overrides):
    policy, store, key, _, approval, _ = case
    payload, signature = signed(approval, key)
    args = dict(payload=payload, signature=signature, policy=policy, store=store, now=NOW)
    args.update(overrides)
    return validate_trusted_staging_decision(**args)


def test_valid_and_reusable_current_snapshot(case):
    checkpoint = ingest(case)
    assert decide(case)["approval_id"] == "id"
    assert decide(case)["approval_id"] == "id"
    assert case[1].value == checkpoint  # Reading does not renew freshness.


@pytest.mark.parametrize("sequence", [0, 1])
def test_replayed_and_lower_sequence_rejected(case, sequence):
    ingest(case)
    case[-1]["sequence_number"] = sequence
    with pytest.raises(AuthorizationRejected, match="rollback"):
        ingest(case)


def test_same_sequence_different_signed_contents_rejected(case):
    ingest(case)
    case[-1]["revoked_approval_ids"] = ["other"]
    with pytest.raises(AuthorizationRejected, match="rollback"):
        ingest(case)


@pytest.mark.parametrize("field, identifier", [("revoked_approval_ids", "id"),
                                                 ("revoked_signing_key_ids", "approval")])
def test_revocation_enforced_and_cannot_be_removed(case, field, identifier):
    case[-1][field] = [identifier]
    ingest(case)
    with pytest.raises(AuthorizationRejected, match="revoked"):
        decide(case)
    case[-1].update(sequence_number=2, **{field: []})
    with pytest.raises(AuthorizationRejected, match="cannot be removed"):
        ingest(case)


def test_cumulative_new_record_survives_consumer_restart(case):
    ingest(case)
    case[-1].update(sequence_number=2, revoked_approval_ids=["other"])
    checkpoint = ingest(case)
    # A fresh caller using the same external state cannot reset its floor.
    assert decide(tuple(case))["approval_id"] == "id"
    case[-1]["sequence_number"] = 1
    with pytest.raises(AuthorizationRejected, match="rollback"):
        ingest(tuple(case))
    assert case[1].value == checkpoint


def test_simulated_external_witness_detects_restored_state(case):
    old = ingest(case)
    case[-1]["sequence_number"] = 2
    ingest(case)
    case[1].value = old
    with pytest.raises(AuthorizationRejected, match="unavailable"):
        decide(case)
    with pytest.raises(AuthorizationRejected, match="unavailable"):
        ingest(case)


@pytest.mark.parametrize("action", [ingest, decide])
def test_missing_state_never_bootstraps(case, action):
    case[1].value = None
    with pytest.raises(AuthorizationRejected, match="missing"):
        action(case)
    assert case[1].value is None


def test_bootstrap_without_signed_record_cannot_authorize(case):
    with pytest.raises(AuthorizationRejected):
        decide(case)


@pytest.mark.parametrize("action", [ingest, decide])
def test_store_outage_denies(case, action, monkeypatch):
    def fail(*args):
        raise TimeoutError("synthetic outage")
    monkeypatch.setattr(case[1], "read", fail)
    with pytest.raises(AuthorizationRejected, match="unavailable"):
        action(case)


@pytest.mark.parametrize("result", [False, None, 1])
def test_failed_or_malformed_cas_denies(case, monkeypatch, result):
    monkeypatch.setattr(case[1], "compare_and_swap", lambda *a: result)
    with pytest.raises(AuthorizationRejected, match="concurrently"):
        ingest(case)


def test_ambiguous_commit_error_denies_then_allows_reread(case, monkeypatch):
    original = case[1].compare_and_swap
    def ambiguous(*args):
        original(*args)
        raise OSError("response lost after commit")
    monkeypatch.setattr(case[1], "compare_and_swap", ambiguous)
    with pytest.raises(AuthorizationRejected, match="commit unavailable"):
        ingest(case)
    assert decide(case)["approval_id"] == "id"
    with pytest.raises(AuthorizationRejected, match="rollback"):
        ingest(case)


def test_concurrent_same_record_has_single_winner(case):
    def attempt(_):
        try:
            ingest(case)
            return True
        except AuthorizationRejected:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(16))) == 1


@pytest.mark.parametrize("field, value", [("authority_id", "unknown"), ("key_id", "approval"),
    ("key_id", "unknown"), ("sequence_number", True), ("sequence_number", 2**63),
    ("issued_at", "bad"), ("expires_at", (NOW + timedelta(minutes=5)).isoformat())])
def test_invalid_or_unknown_revocation_denied_without_mutation(case, field, value):
    original = case[1].value
    case[-1][field] = value
    with pytest.raises(AuthorizationRejected):
        ingest(case)
    assert case[1].value == original


def test_tampered_record_denies(case):
    payload, sig = signed(case[-1], case[3])
    with pytest.raises(AuthorizationRejected, match="signature"):
        ingest(case, payload=payload.replace(b'"sequence_number": 1', b'"sequence_number": 2'), signature=sig)


@pytest.mark.parametrize("field, value", [("deployment_id", "attacker"), ("environment", "production"),
    ("audience", "public"), ("database_sha256", "b" * 64), ("release_id", "wrong"),
    ("issued_at", (NOW + timedelta(seconds=1)).isoformat()),
    ("expires_at", (NOW + timedelta(hours=24)).isoformat())])
def test_wrong_scope_or_time_denied(case, field, value):
    ingest(case)
    case[-2][field] = value
    with pytest.raises(AuthorizationRejected):
        decide(case)


def test_wrong_approval_signature_denies(case):
    ingest(case)
    payload, _ = signed(case[-2], case[2])
    with pytest.raises(AuthorizationRejected, match="signature"):
        decide(case, signature=Ed25519PrivateKey.generate().sign(payload))


@pytest.mark.parametrize("role", ["approval_keys", "revocation_keys"])
def test_policy_emergency_revocation_denies(case, role):
    ingest(case)
    keys = {k: replace(v, revoked=True) for k, v in getattr(case[0], role).items()}
    policy = replace(case[0], **{role: keys})
    with pytest.raises(AuthorizationRejected, match="revoked"):
        decide(case, policy=policy)
    if role == "revocation_keys":
        case[-1]["sequence_number"] = 2
        with pytest.raises(AuthorizationRejected, match="revoked"):
            ingest(case, policy=policy)


@pytest.mark.parametrize("role, index, key_id", [("approval_keys", -2, "approval"),
                                                ("revocation_keys", -1, "revocation")])
def test_key_validity_boundaries_and_overlap_rotation(case, role, index, key_id):
    rotated = Ed25519PrivateKey.generate()
    old = getattr(case[0], role)[key_id]
    keys = {key_id: old, "rotated": LifecycleKey(rotated.public_key(), NOW, NOW + timedelta(hours=1))}
    policy = replace(case[0], **{role: keys})
    if role == "approval_keys":
        ingest(case)
        decide(case, policy=policy)  # Old key remains usable during overlap.
    document = case[index]
    document.update(key_id="rotated", issued_at=NOW.isoformat())
    payload, signature = signed(document, rotated)
    action = decide if role == "approval_keys" else ingest
    action(case, policy=policy, payload=payload, signature=signature)  # Inclusive start.
    document["issued_at"] = (NOW - timedelta(microseconds=1)).isoformat()
    payload, signature = signed(document, rotated)
    if role == "revocation_keys":
        document["sequence_number"] = 2
        payload, signature = signed(document, rotated)
    with pytest.raises(AuthorizationRejected, match="key validity"):
        action(case, policy=policy, payload=payload, signature=signature)
    expired_policy = replace(policy, **{role: {key_id: replace(old, not_after=NOW)}})
    document["key_id"] = key_id
    if role == "revocation_keys":
        document["sequence_number"] = 2
    with pytest.raises(AuthorizationRejected):
        action(case, policy=expired_policy)


def test_policy_copies_key_maps_and_enforces_role_isolation(case):
    keys = dict(case[0].approval_keys)
    policy = replace(case[0], approval_keys=keys)
    keys.clear()
    assert "approval" in policy.approval_keys
    with pytest.raises(TypeError):
        policy.approval_keys["evil"] = next(iter(case[0].approval_keys.values()))
    with pytest.raises(ValueError, match="separate"):
        replace(policy, revocation_keys={"other-id": policy.approval_keys["approval"]})


@pytest.mark.parametrize("delta", [timedelta(minutes=3), timedelta(minutes=4)])
def test_stale_cached_record_denies_and_replay_cannot_refresh(case, delta):
    ingest(case)
    with pytest.raises(AuthorizationRejected):
        decide(case, now=NOW + delta)
    with pytest.raises(AuthorizationRejected):
        ingest(case, now=NOW + delta)


def test_corrupt_checkpoint_and_concurrent_decision_denied(case, monkeypatch):
    checkpoint = ingest(case)
    case[1].value = replace(checkpoint, revoked_approval_ids=frozenset({"forged"}))
    with pytest.raises(AuthorizationRejected, match="inconsistent"):
        decide(case)
    calls = iter([checkpoint, replace(checkpoint, sequence_number=2)])
    monkeypatch.setattr(case[1], "read", lambda *a: next(calls))
    with pytest.raises(AuthorizationRejected, match="changed during"):
        decide(case)


def test_offline_success_does_not_bypass_hosted_gate(case, monkeypatch):
    from app.db.pharma.release_connection import connect_release, PharmaceuticalReleaseUnavailable
    ingest(case)
    assert decide(case)
    for mode in ("staging", "production", "preview"):
        monkeypatch.setenv("DAVAI_ENV", mode)
        with pytest.raises(PharmaceuticalReleaseUnavailable, match="not authorized"):
            connect_release()


@pytest.mark.parametrize("role", ["approval_keys", "revocation_keys"])
def test_aliases_cannot_bypass_key_id_revocation(case, role):
    keys = dict(getattr(case[0], role))
    keys["alias"] = next(iter(keys.values()))
    with pytest.raises(ValueError, match="aliases"):
        replace(case[0], **{role: keys})


@pytest.mark.parametrize("role, action, key_id", [("approval_keys", decide, "approval"),
                                                ("revocation_keys", ingest, "revocation")])
def test_document_expiry_may_equal_key_expiry(case, role, action, key_id):
    if role == "approval_keys":
        ingest(case)
    document = case[-2] if role == "approval_keys" else case[-1]
    expiry = datetime.fromisoformat(document["expires_at"])
    old = getattr(case[0], role)[key_id]
    policy = replace(case[0], **{role: {key_id: replace(old, not_after=expiry)}})
    action(case, policy=policy)
    if role == "revocation_keys":
        case[-1]["sequence_number"] = 2
    document["expires_at"] = (expiry + timedelta(microseconds=1)).isoformat()
    with pytest.raises(AuthorizationRejected, match="key validity"):
        action(case, policy=policy)


def test_expired_checkpoint_can_advance_without_removing_tombstones(case):
    case[-1]["revoked_approval_ids"] = ["old-tombstone"]
    ingest(case)
    later = NOW + timedelta(minutes=4)
    case[-1].update(sequence_number=2, issued_at=later.isoformat(),
                    expires_at=(later + timedelta(minutes=4)).isoformat())
    ingest(case, now=later)
    assert decide(case, now=later)["approval_id"] == "id"


def test_emergency_authority_rotation_recovers_with_higher_cumulative_snapshot(case):
    case[-1]["revoked_approval_ids"] = ["old-tombstone"]
    ingest(case)
    new_key = Ed25519PrivateKey.generate()
    old = case[0].revocation_keys["revocation"]
    policy = replace(case[0], revocation_keys={
        "revocation": replace(old, revoked=True),
        "new-authority-key": replace(old, public_key=new_key.public_key()),
    })
    with pytest.raises(AuthorizationRejected, match="revoked"):
        decide(case, policy=policy)
    case[-1].update(sequence_number=2, key_id="new-authority-key")
    payload, signature = signed(case[-1], new_key)
    ingest(case, policy=policy, payload=payload, signature=signature)
    assert decide(case, policy=policy)["approval_id"] == "id"
