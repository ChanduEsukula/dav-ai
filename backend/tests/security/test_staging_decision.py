import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security.staging_decision import validate_signed_staging_decision
from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)
RELEASE = "dav-ai-pharma-v1-phase4b-communications-20261006"
SHA = "87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71"


def attempt(
    *,
    revoked_approvals=(),
    revoked_keys=(),
    tamper_revocation=False,
    sequence=10,
    authority="test-authority",
):
    approval_key = Ed25519PrivateKey.generate()
    revocation_key = Ed25519PrivateKey.generate()

    approval = {
        "approval_id": "approval-001",
        "key_id": "approval-key",
        "release_id": RELEASE,
        "database_sha256": SHA,
        "environment": "staging",
        "audience": "private",
        "deployment_id": "test-deployment",
        "issued_at": (NOW - timedelta(minutes=1)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=30)).isoformat(),
    }

    revocation = {
        "schema_version": "1",
        "authority_id": authority,
        "key_id": "revocation-key",
        "sequence_number": sequence,
        "issued_at": (NOW - timedelta(minutes=1)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=3)).isoformat(),
        "revoked_approval_ids": list(revoked_approvals),
        "revoked_signing_key_ids": list(revoked_keys),
    }

    approval_bytes = json.dumps(approval, sort_keys=True).encode()
    revocation_bytes = json.dumps(revocation, sort_keys=True).encode()

    approval_sig = approval_key.sign(approval_bytes)
    revocation_sig = revocation_key.sign(revocation_bytes)

    if tamper_revocation:
        revocation_bytes = revocation_bytes.replace(
            b'"sequence_number": 10',
            b'"sequence_number": 11',
        )

    return validate_signed_staging_decision(
        approval_payload=approval_bytes,
        approval_signature=approval_sig,
        approval_registry=TrustedKeyRegistry({
            "approval-key": approval_key.public_key(),
        }),
        revocation_payload=revocation_bytes,
        revocation_signature=revocation_sig,
        revocation_registry=TrustedKeyRegistry({
            "revocation-key": revocation_key.public_key(),
        }),
        expected_authority_id="test-authority",
        minimum_sequence=10,
        expected_release_id=RELEASE,
        expected_database_sha256=SHA,
        expected_deployment_id="test-deployment",
        now=NOW,
    )


def test_valid_signed_decision():
    assert attempt()["approval_id"] == "approval-001"


def test_revoked_approval_denied():
    with pytest.raises(AuthorizationRejected, match="Approval has been revoked"):
        attempt(revoked_approvals=("approval-001",))


def test_revoked_signing_key_denied():
    with pytest.raises(AuthorizationRejected, match="signing key has been revoked"):
        attempt(revoked_keys=("approval-key",))


def test_modified_revocation_signature_denied():
    with pytest.raises(AuthorizationRejected, match="signature"):
        attempt(tamper_revocation=True)


def test_revocation_sequence_rollback_denied():
    with pytest.raises(AuthorizationRejected, match="rollback"):
        attempt(sequence=9)
