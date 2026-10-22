"""Explicitly trusted Ed25519 keys for staging approval verification.

This module does not authorize pharmaceutical database serving.
"""

from collections.abc import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.security.staging_authorization import AuthorizationRejected


class TrustedKeyRegistry:
    def __init__(self, keys: Mapping[str, Ed25519PublicKey]):
        if not keys:
            raise ValueError("Trusted key registry cannot be empty")

        self._keys = {}

        for key_id, public_key in keys.items():
            if not isinstance(key_id, str) or not key_id:
                raise ValueError("Invalid trusted key identifier")

            if not isinstance(public_key, Ed25519PublicKey):
                raise ValueError("Invalid trusted public key")

            self._keys[key_id] = public_key

    def resolve(self, key_id: str) -> Ed25519PublicKey:
        if not isinstance(key_id, str) or not key_id:
            raise AuthorizationRejected("Invalid signing key identifier")

        try:
            return self._keys[key_id]
        except KeyError as exc:
            raise AuthorizationRejected(
                "Untrusted signing key identifier"
            ) from exc


def verify_with_trusted_keys(
    *,
    payload: bytes,
    signature: bytes,
    registry: TrustedKeyRegistry,
    expected_release_id: str,
    expected_database_sha256: str,
    expected_deployment_id: str,
    now=None,
) -> dict:
    """Verify an approval using a registry-selected trusted key."""

    from app.security.validation import parse_document

    from app.security.staging_authorization import (
        verify_staging_authorization,
    )

    untrusted_claims = parse_document(
        payload, limit=8192, label="authorization",
        duplicate="Duplicate authorization claim",
    )

    key_id = untrusted_claims.get("key_id")
    public_key = registry.resolve(key_id)

    return verify_staging_authorization(
        payload=payload,
        signature=signature,
        public_key=public_key,
        expected_release_id=expected_release_id,
        expected_database_sha256=expected_database_sha256,
        expected_deployment_id=expected_deployment_id,
        now=now,
    )
