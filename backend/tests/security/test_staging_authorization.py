import copy
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security.staging_authorization import (
    AuthorizationRejected,
    verify_staging_authorization,
)


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)
RELEASE_ID = "dav-ai-pharma-v1-phase4b-communications-20261006"
DATABASE_SHA256 = "87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71"
DEPLOYMENT_ID = "synthetic-private-staging-01"


@pytest.fixture
def private_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def claims():
    return {
        "approval_id": "test-approval-001",
        "key_id": "test-key-001",
        "release_id": RELEASE_ID,
        "database_sha256": DATABASE_SHA256,
        "environment": "staging",
        "audience": "private",
        "deployment_id": DEPLOYMENT_ID,
        "issued_at": (NOW - timedelta(minutes=5)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=30)).isoformat(),
    }


def verify(claims, private_key, *, signature=None, **overrides):
    payload = json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    if signature is None:
        signature = private_key.sign(payload)

    arguments = {
        "payload": payload,
        "signature": signature,
        "public_key": private_key.public_key(),
        "expected_release_id": RELEASE_ID,
        "expected_database_sha256": DATABASE_SHA256,
        "expected_deployment_id": DEPLOYMENT_ID,
        "now": NOW,
    }
    arguments.update(overrides)

    return verify_staging_authorization(**arguments)


def test_valid_signed_authorization(claims, private_key):
    result = verify(claims, private_key)
    assert result["approval_id"] == "test-approval-001"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("environment", "production"),
        ("audience", "public"),
        ("release_id", "wrong-release"),
        ("database_sha256", "0" * 64),
        ("deployment_id", "other-deployment"),
        ("issued_at", "2026-10-22T16:00:00+00:00"),
        ("expires_at", "2026-10-22T14:00:00+00:00"),
        ("expires_at", "invalid-date"),
        ("approval_id", ""),
    ],
)
def test_invalid_claims_rejected(claims, private_key, field, invalid_value):
    modified = copy.deepcopy(claims)
    modified[field] = invalid_value

    with pytest.raises(AuthorizationRejected):
        verify(modified, private_key)


def test_tampered_signature_rejected(claims, private_key):
    payload = json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    signature = private_key.sign(payload)

    modified = dict(claims)
    modified["deployment_id"] = "unauthorized-deployment"

    with pytest.raises(AuthorizationRejected):
        verify(modified, private_key, signature=signature)


def test_wrong_signing_key_rejected(claims, private_key):
    other_key = Ed25519PrivateKey.generate()

    payload = json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    signature = other_key.sign(payload)

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key, signature=signature)


def test_missing_claim_rejected(claims, private_key):
    del claims["approval_id"]

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key)


def test_additional_claim_rejected(claims, private_key):
    claims["allow_production"] = True

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key)


def test_naive_verification_clock_rejected(claims, private_key):
    with pytest.raises(AuthorizationRejected):
        verify(
            claims,
            private_key,
            now=datetime(2026, 10, 22, 15, 0),
        )


def test_expired_at_exact_boundary(claims, private_key):
    expiry = datetime.fromisoformat(claims["expires_at"])

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key, now=expiry)


def test_duplicate_json_claims_rejected(claims, private_key):
    valid_payload = json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    )

    duplicated_payload = valid_payload.replace(
        '"environment":"staging"',
        '"environment":"production","environment":"staging"',
    ).encode("utf-8")

    signature = private_key.sign(duplicated_payload)

    with pytest.raises(
        AuthorizationRejected, match="Duplicate authorization claim"
    ):
        verify_staging_authorization(
            payload=duplicated_payload,
            signature=signature,
            public_key=private_key.public_key(),
            expected_release_id=RELEASE_ID,
            expected_database_sha256=DATABASE_SHA256,
            expected_deployment_id=DEPLOYMENT_ID,
            now=NOW,
        )


def test_excessive_authorization_lifetime_rejected(claims, private_key):
    claims["expires_at"] = (
        NOW + timedelta(days=365)
    ).isoformat()

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key)


def test_non_string_claim_rejected(claims, private_key):
    claims["approval_id"] = 123

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key)


def test_naive_issued_at_rejected(claims, private_key):
    claims["issued_at"] = "2026-10-22T14:55:00"

    with pytest.raises(AuthorizationRejected):
        verify(claims, private_key)
