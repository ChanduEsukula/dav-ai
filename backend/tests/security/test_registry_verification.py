import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import (
    TrustedKeyRegistry,
    verify_with_trusted_keys,
)


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)
RELEASE = "dav-ai-pharma-v1-phase4b-communications-20261006"
SHA256 = "87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71"
DEPLOYMENT = "synthetic-private-staging-01"


def make_claims(key_id="trusted-key"):
    return {
        "approval_id": "synthetic-approval",
        "key_id": key_id,
        "release_id": RELEASE,
        "database_sha256": SHA256,
        "environment": "staging",
        "audience": "private",
        "deployment_id": DEPLOYMENT,
        "issued_at": (NOW - timedelta(minutes=5)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=30)).isoformat(),
    }


def check(payload, signature, registry):
    return verify_with_trusted_keys(
        payload=payload,
        signature=signature,
        registry=registry,
        expected_release_id=RELEASE,
        expected_database_sha256=SHA256,
        expected_deployment_id=DEPLOYMENT,
        now=NOW,
    )


def encode(claims):
    return json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    ).encode()


def test_valid_registry_bound_signature():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key()
    })

    payload = encode(make_claims())
    result = check(payload, signer.sign(payload), registry)

    assert result["key_id"] == "trusted-key"


def test_unknown_key_id_rejected():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key()
    })

    payload = encode(make_claims("unknown-key"))

    with pytest.raises(AuthorizationRejected):
        check(payload, signer.sign(payload), registry)


def test_key_id_must_match_actual_signer():
    signer_a = Ed25519PrivateKey.generate()
    signer_b = Ed25519PrivateKey.generate()

    registry = TrustedKeyRegistry({
        "key-a": signer_a.public_key(),
        "key-b": signer_b.public_key(),
    })

    payload = encode(make_claims("key-b"))

    with pytest.raises(
        AuthorizationRejected, match="Invalid authorization signature"
    ):
        check(payload, signer_a.sign(payload), registry)


def test_tampered_key_id_rejected():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key(),
        "other-key": Ed25519PrivateKey.generate().public_key(),
    })

    original = encode(make_claims())
    signature = signer.sign(original)

    modified = encode(make_claims("other-key"))

    with pytest.raises(AuthorizationRejected):
        check(modified, signature, registry)


def test_non_string_key_id_rejected():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key()
    })

    payload = encode(make_claims(123))

    with pytest.raises(AuthorizationRejected):
        check(payload, signer.sign(payload), registry)


def test_duplicate_key_id_rejected():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key()
    })

    payload = encode(make_claims()).replace(
        b'"key_id":"trusted-key"',
        b'"key_id":"unknown","key_id":"trusted-key"',
    )

    with pytest.raises(
        AuthorizationRejected, match="Duplicate authorization claim"
    ):
        check(payload, signer.sign(payload), registry)


def test_oversized_document_rejected():
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({
        "trusted-key": signer.public_key()
    })

    payload = b"x" * 8193

    with pytest.raises(
        AuthorizationRejected, match="Invalid authorization payload size"
    ):
        check(payload, signer.sign(payload), registry)
