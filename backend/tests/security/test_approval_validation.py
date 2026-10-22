import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from app.security.approval_validation import validate_offline_approval
from app.security.revocation import RevocationSnapshot
from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)
RELEASE = "dav-ai-pharma-v1-phase4b-communications-20261006"
SHA = "87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71"


def attempt(*, revoked=False, snapshot_present=True, tampered=False):
    signer = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry({"test-key": signer.public_key()})

    claims = {
        "approval_id": "approval-001",
        "key_id": "test-key",
        "release_id": RELEASE,
        "database_sha256": SHA,
        "environment": "staging",
        "audience": "private",
        "deployment_id": "test-deployment",
        "issued_at": (NOW - timedelta(minutes=1)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=30)).isoformat(),
    }

    payload = json.dumps(claims, sort_keys=True).encode()
    signature = signer.sign(payload)

    if tampered:
        payload = payload.replace(b"test-deployment", b"evil-deployment")

    snapshot = None
    if snapshot_present:
        snapshot = RevocationSnapshot(
            fetched_at=NOW - timedelta(seconds=30),
            revoked_approval_ids=frozenset(
                {"approval-001"} if revoked else set()
            ),
        )

    return validate_offline_approval(
        payload=payload,
        signature=signature,
        registry=registry,
        revocation_snapshot=snapshot,
        expected_release_id=RELEASE,
        expected_database_sha256=SHA,
        expected_deployment_id="test-deployment",
        now=NOW,
    )


def test_valid_approval_passes_all_checks():
    assert attempt()["approval_id"] == "approval-001"


def test_revoked_approval_rejected():
    with pytest.raises(AuthorizationRejected):
        attempt(revoked=True)


def test_missing_revocation_state_rejected():
    with pytest.raises(AuthorizationRejected):
        attempt(snapshot_present=False)


def test_tampered_approval_rejected():
    with pytest.raises(AuthorizationRejected):
        attempt(tampered=True)
