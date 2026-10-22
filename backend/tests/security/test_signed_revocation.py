import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security.signed_revocation import verify_signed_revocation
from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)


def make_record():
    return {
        "schema_version": "1",
        "authority_id": "test-revocation-authority",
        "key_id": "test-revocation-key",
        "sequence_number": 10,
        "issued_at": (NOW - timedelta(minutes=1)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=3)).isoformat(),
        "revoked_approval_ids": ["approval-revoked"],
        "revoked_signing_key_ids": ["key-revoked"],
    }


def check(record, *, signing_key=None, floor=10, signature=None):
    key = signing_key or Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "test-revocation-key": key.public_key()
    })

    payload = json.dumps(record, sort_keys=True).encode()
    signature = signature if signature is not None else key.sign(payload)

    return verify_signed_revocation(
        payload=payload,
        signature=signature,
        registry=registry,
        expected_authority_id="test-revocation-authority",
        minimum_sequence=floor,
        now=NOW,
    )


def test_valid_revocation_record():
    assert check(make_record())["sequence_number"] == 10


def test_rollback_rejected():
    with pytest.raises(AuthorizationRejected, match="rollback"):
        check(make_record(), floor=11)


def test_wrong_authority_rejected():
    record = make_record()
    record["authority_id"] = "untrusted-authority"
    with pytest.raises(AuthorizationRejected):
        check(record)


def test_expired_record_rejected():
    record = make_record()
    record["expires_at"] = (NOW - timedelta(seconds=1)).isoformat()
    with pytest.raises(AuthorizationRejected):
        check(record)


def test_excessive_lifetime_rejected():
    record = make_record()
    record["expires_at"] = (NOW + timedelta(hours=1)).isoformat()
    with pytest.raises(AuthorizationRejected):
        check(record)


def test_duplicate_revocation_ids_rejected():
    record = make_record()
    record["revoked_approval_ids"] = ["a", "a"]
    with pytest.raises(AuthorizationRejected):
        check(record)


def test_boolean_sequence_rejected():
    record = make_record()
    record["sequence_number"] = True
    with pytest.raises(AuthorizationRejected):
        check(record)


def test_modified_payload_rejected():
    key = Ed25519PrivateKey.generate()
    original = json.dumps(make_record(), sort_keys=True).encode()
    signature = key.sign(original)

    modified = make_record()
    modified["sequence_number"] = 11

    with pytest.raises(AuthorizationRejected, match="signature"):
        check(modified, signing_key=key, signature=signature)


def test_unknown_revocation_key_rejected():
    key = Ed25519PrivateKey.generate()
    record = make_record()
    record["key_id"] = "unknown-key"

    with pytest.raises(AuthorizationRejected):
        check(record, signing_key=key)


def test_duplicate_revocation_json_fields_rejected():
    key = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "test-revocation-key": key.public_key()
    })

    payload = json.dumps(make_record(), sort_keys=True).replace(
        '"sequence_number": 10',
        '"sequence_number": 9, "sequence_number": 10',
    ).encode()

    with pytest.raises(
        AuthorizationRejected, match="Duplicate revocation field"
    ):
        verify_signed_revocation(
            payload=payload,
            signature=key.sign(payload),
            registry=registry,
            expected_authority_id="test-revocation-authority",
            minimum_sequence=10,
            now=NOW,
        )


def test_nan_revocation_sequence_rejected():
    record = make_record()
    record["sequence_number"] = float("nan")

    with pytest.raises(AuthorizationRejected):
        check(record)


def test_null_revocation_key_rejected():
    record = make_record()
    record["key_id"] = None

    with pytest.raises(AuthorizationRejected):
        check(record)
