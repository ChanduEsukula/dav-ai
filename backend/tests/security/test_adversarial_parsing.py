import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security.staging_authorization import AuthorizationRejected, verify_staging_authorization
from app.security.signed_revocation import verify_signed_revocation
from app.security.trusted_keys import TrustedKeyRegistry, verify_with_trusted_keys
from app.security.revocation import RevocationSnapshot, check_revocation

NOW = datetime(2026, 10, 22, 15, tzinfo=timezone.utc)


@pytest.fixture(params=["direct", "registry", "revocation"])
def verifier(request):
    key = Ed25519PrivateKey.generate()
    if request.param == "revocation":
        document = dict(schema_version="1", authority_id="authority", key_id="key", sequence_number=1,
                        issued_at=(NOW - timedelta(minutes=1)).isoformat(),
                        expires_at=(NOW + timedelta(minutes=3)).isoformat(),
                        revoked_approval_ids=[], revoked_signing_key_ids=[])
        def verify(payload, signature=None, now=NOW):
            return verify_signed_revocation(payload=payload, signature=key.sign(payload) if signature is None else signature,
                registry=TrustedKeyRegistry({"key": key.public_key()}), expected_authority_id="authority",
                minimum_sequence=0, now=now)
    else:
        document = dict(approval_id="id", key_id="key", release_id="release", database_sha256="a" * 64,
                        deployment_id="deployment", environment="staging", audience="private",
                        issued_at=(NOW - timedelta(minutes=1)).isoformat(),
                        expires_at=(NOW + timedelta(minutes=3)).isoformat())
        def verify(payload, signature=None, now=NOW):
            args = dict(payload=payload, signature=key.sign(payload) if signature is None else signature,
                        expected_release_id="release", expected_database_sha256="a" * 64,
                        expected_deployment_id="deployment", now=now)
            if request.param == "direct":
                return verify_staging_authorization(**args, public_key=key.public_key())
            return verify_with_trusted_keys(**args, registry=TrustedKeyRegistry({"key": key.public_key()}))
    return document, verify


@pytest.mark.parametrize("payload", [b"", b"null", b"[]", b"{", b'\xff', b'{"x":NaN}',
    b'{"x":Infinity}', b'{"x":' + b'1' * 5000 + b'}', b'[' * 2000 + b']' * 2000,
    b'{"key_id":"key","key_id":"key"}', b'{"x":{"nested":1,"nested":2}}', b'x' * 65537])
def test_malformed_documents_rejected_consistently(verifier, payload):
    with pytest.raises(AuthorizationRejected):
        verifier[1](payload)


@pytest.mark.parametrize("value", ["2026-10-22", "2026-10-22 14:59:00+00:00", "2026-W43-4T14:59:00Z",
    "2026-10-22T14:59:00", "2026-10-22T14:59:00+00:60", "2026-10-22T14:59:00+24:00",
    "2026-02-30T14:59:00Z", "0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00",
    "2026-10-22T14:59:60Z", "2026-10-22T14:59:00.0000001Z", None, 123])
def test_malformed_timestamps_do_not_escape_rejection(verifier, value):
    document, verify = verifier
    document["issued_at"] = value
    with pytest.raises(AuthorizationRejected):
        verify(json.dumps(document).encode())


@pytest.mark.parametrize("signature", [b"", b"x" * 63, b"x" * 65, "x" * 64, bytearray(64), 123])
def test_signature_types_and_lengths_rejected(verifier, signature):
    document, verify = verifier
    with pytest.raises(AuthorizationRejected):
        verify(json.dumps(document).encode(), signature=signature)


@pytest.mark.parametrize("now", ["now", 123, datetime(2026, 10, 22),
    datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=1)))])
def test_invalid_verification_clock_rejected(verifier, now):
    document, verify = verifier
    with pytest.raises(AuthorizationRejected):
        verify(json.dumps(document).encode(), now=now)


def test_utf16_not_accepted(verifier):
    document, verify = verifier
    with pytest.raises(AuthorizationRejected):
        verify(json.dumps(document).encode("utf-16"))


@pytest.mark.parametrize("snapshot", [None, {}, RevocationSnapshot("today", frozenset()),
    RevocationSnapshot(NOW, ["id"]), RevocationSnapshot(NOW, frozenset({123}))])
def test_legacy_unsigned_snapshot_malformed_rejected(snapshot):
    with pytest.raises(AuthorizationRejected):
        check_revocation("id", snapshot, now=NOW)


@pytest.mark.parametrize("payload", [None, "{}", bytearray(b"{}"), 123])
def test_payload_type_rejected(verifier, payload):
    with pytest.raises(AuthorizationRejected):
        verifier[1](payload, signature=b"x" * 64)


@pytest.mark.parametrize("expiry_delta", [timedelta(0), timedelta(minutes=-1), timedelta(days=2)])
def test_invalid_document_lifetimes(verifier, expiry_delta):
    document, verify = verifier
    issued = datetime.fromisoformat(document["issued_at"])
    document["expires_at"] = (issued + expiry_delta).isoformat()
    with pytest.raises(AuthorizationRejected):
        verify(json.dumps(document).encode())


def test_positive_explicit_offset_and_lifetime_boundary(verifier):
    document, verify = verifier
    local = timezone(timedelta(hours=-5))
    document["issued_at"] = (NOW - timedelta(minutes=1)).astimezone(local).isoformat()
    # All verifier variants accept the exact five-minute revocation lifetime.
    document["expires_at"] = (NOW + timedelta(minutes=4)).astimezone(local).isoformat()
    assert verify(json.dumps(document).encode())
