"""Combined offline approval checks. Not authorized for deployment."""

from datetime import datetime

from app.security.revocation import RevocationSnapshot, check_revocation
from app.security.trusted_keys import (
    TrustedKeyRegistry,
    verify_with_trusted_keys,
)


def validate_offline_approval(
    *,
    payload: bytes,
    signature: bytes,
    registry: TrustedKeyRegistry,
    revocation_snapshot: RevocationSnapshot | None,
    expected_release_id: str,
    expected_database_sha256: str,
    expected_deployment_id: str,
    now: datetime | None = None,
) -> dict:
    """Require signature, claims, and revocation checks to pass."""

    claims = verify_with_trusted_keys(
        payload=payload,
        signature=signature,
        registry=registry,
        expected_release_id=expected_release_id,
        expected_database_sha256=expected_database_sha256,
        expected_deployment_id=expected_deployment_id,
        now=now,
    )

    check_revocation(
        claims["approval_id"],
        revocation_snapshot,
        now=now,
    )

    return claims
