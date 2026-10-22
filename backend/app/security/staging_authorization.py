"""Offline verification of private-staging approval documents.

This module does not grant permission to serve pharmaceutical data.
"""

from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.security.validation import (
    AuthorizationRejected,
    check_signature_input,
    parse_document,
    parse_timestamp,
    utc_time,
)


REQUIRED_CLAIMS = frozenset({
    "approval_id",
    "key_id",
    "release_id",
    "database_sha256",
    "environment",
    "audience",
    "deployment_id",
    "issued_at",
    "expires_at",
})


def verify_staging_authorization(
    *,
    payload: bytes,
    signature: bytes,
    public_key: Ed25519PublicKey,
    expected_release_id: str,
    expected_database_sha256: str,
    expected_deployment_id: str,
    now: datetime | None = None,
) -> dict:
    """Validate the exact signed bytes and mandatory staging claims."""

    claims = parse_document(payload, limit=8192, label="authorization",
                            duplicate="Duplicate authorization claim")
    check_signature_input(signature)
    if not isinstance(public_key, Ed25519PublicKey):
        raise AuthorizationRejected("Invalid trusted public key")
    try:
        public_key.verify(signature, payload)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise AuthorizationRejected("Invalid authorization signature") from exc

    if set(claims) != REQUIRED_CLAIMS:
        raise AuthorizationRejected("Unexpected authorization claims")

    if any(type(value) is not str or not value for value in claims.values()):
        raise AuthorizationRejected("Authorization claims must be nonempty strings")

    if claims["environment"] != "staging":
        raise AuthorizationRejected("Unauthorized environment")

    if claims["audience"] != "private":
        raise AuthorizationRejected("Unauthorized audience")

    if claims["release_id"] != expected_release_id:
        raise AuthorizationRejected("Wrong pharmaceutical release")

    if claims["database_sha256"] != expected_database_sha256:
        raise AuthorizationRejected("Wrong pharmaceutical artifact")

    if claims["deployment_id"] != expected_deployment_id:
        raise AuthorizationRejected("Wrong staging deployment")

    issued = parse_timestamp(claims["issued_at"])
    expires = parse_timestamp(claims["expires_at"])
    current = utc_time(now if now is not None else datetime.now(timezone.utc))

    if not issued <= current < expires:
        raise AuthorizationRejected("Authorization is not currently valid")

    if expires <= issued:
        raise AuthorizationRejected("Invalid authorization lifetime")

    if expires - issued > timedelta(hours=24):
        raise AuthorizationRejected("Authorization lifetime exceeds 24 hours")

    return claims
