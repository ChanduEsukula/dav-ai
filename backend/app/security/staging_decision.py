"""Isolated signed-approval and signed-revocation validation.

This module does not authorize deployed pharmaceutical serving.
"""

from datetime import datetime

from app.security.signed_revocation import verify_signed_revocation
from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import (
    TrustedKeyRegistry,
    verify_with_trusted_keys,
)


def validate_signed_staging_decision(
    *,
    approval_payload: bytes,
    approval_signature: bytes,
    approval_registry: TrustedKeyRegistry,
    revocation_payload: bytes,
    revocation_signature: bytes,
    revocation_registry: TrustedKeyRegistry,
    expected_authority_id: str,
    minimum_sequence: int,
    expected_release_id: str,
    expected_database_sha256: str,
    expected_deployment_id: str,
    now: datetime | None = None,
) -> dict:
    """Require authentic, current, non-revoked approval and signer."""

    record = verify_signed_revocation(
        payload=revocation_payload,
        signature=revocation_signature,
        registry=revocation_registry,
        expected_authority_id=expected_authority_id,
        minimum_sequence=minimum_sequence,
        now=now,
    )

    claims = verify_with_trusted_keys(
        payload=approval_payload,
        signature=approval_signature,
        registry=approval_registry,
        expected_release_id=expected_release_id,
        expected_database_sha256=expected_database_sha256,
        expected_deployment_id=expected_deployment_id,
        now=now,
    )

    if claims["approval_id"] in record["revoked_approval_ids"]:
        raise AuthorizationRejected("Approval has been revoked")

    if claims["key_id"] in record["revoked_signing_key_ids"]:
        raise AuthorizationRejected("Approval signing key has been revoked")

    return claims
