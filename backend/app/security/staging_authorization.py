"""Offline verification of private-staging approval documents.

This module does not grant permission to serve pharmaceutical data.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class AuthorizationRejected(ValueError):
    """A staging authorization did not pass verification."""


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

    try:
        public_key.verify(signature, payload)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise AuthorizationRejected("Invalid authorization signature") from exc

    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuthorizationRejected("Duplicate authorization claim")
            result[key] = value
        return result

    try:
        claims = json.loads(
            payload,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                AuthorizationRejected("Invalid JSON constant")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthorizationRejected("Invalid authorization document") from exc

    if not isinstance(claims, dict):
        raise AuthorizationRejected("Authorization claims must be an object")

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

    def parse_time(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise AuthorizationRejected("Invalid authorization timestamp") from exc

        if parsed.tzinfo is None:
            raise AuthorizationRejected("Authorization timestamp lacks timezone")

        return parsed.astimezone(timezone.utc)

    issued = parse_time(claims["issued_at"])
    expires = parse_time(claims["expires_at"])

    current = now or datetime.now(timezone.utc)

    if current.tzinfo is None:
        raise AuthorizationRejected("Verification clock lacks timezone")

    current = current.astimezone(timezone.utc)

    if not issued <= current < expires:
        raise AuthorizationRejected("Authorization is not currently valid")

    if expires <= issued:
        raise AuthorizationRejected("Invalid authorization lifetime")

    if expires - issued > timedelta(hours=24):
        raise AuthorizationRejected("Authorization lifetime exceeds 24 hours")

    return claims
