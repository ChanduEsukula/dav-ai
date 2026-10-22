"""Verify signed revocation records without authorizing deployment."""

import json
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature

from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry


MAX_RECORD_LIFETIME = timedelta(minutes=5)

REQUIRED_FIELDS = frozenset({
    "schema_version",
    "authority_id",
    "key_id",
    "sequence_number",
    "issued_at",
    "expires_at",
    "revoked_approval_ids",
    "revoked_signing_key_ids",
})


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuthorizationRejected("Duplicate revocation field")
        result[key] = value
    return result


def _parse_timestamp(value):
    if not isinstance(value, str):
        raise AuthorizationRejected("Invalid revocation timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationRejected("Invalid revocation timestamp") from exc

    if parsed.tzinfo is None:
        raise AuthorizationRejected("Revocation timestamp lacks timezone")

    return parsed.astimezone(timezone.utc)


def verify_signed_revocation(
    *,
    payload: bytes,
    signature: bytes,
    registry: TrustedKeyRegistry,
    expected_authority_id: str,
    minimum_sequence: int,
    now: datetime | None = None,
) -> dict:
    """Validate signed bytes, authority, timestamps and sequence floor."""

    if not isinstance(payload, bytes) or len(payload) > 65536:
        raise AuthorizationRejected("Invalid revocation payload size")

    try:
        record = json.loads(
            payload,
            object_pairs_hook=_reject_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                AuthorizationRejected("Invalid revocation JSON constant")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthorizationRejected("Invalid revocation JSON") from exc

    if not isinstance(record, dict) or set(record) != REQUIRED_FIELDS:
        raise AuthorizationRejected("Invalid revocation record shape")

    key_id = record["key_id"]
    if not isinstance(key_id, str) or not key_id:
        raise AuthorizationRejected("Invalid revocation key identifier")

    public_key = registry.resolve(key_id)

    try:
        public_key.verify(signature, payload)
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise AuthorizationRejected("Invalid revocation signature") from exc

    if record["schema_version"] != "1":
        raise AuthorizationRejected("Unsupported revocation schema")

    if record["authority_id"] != expected_authority_id:
        raise AuthorizationRejected("Wrong revocation authority")

    sequence = record["sequence_number"]
    if type(sequence) is not int or sequence < 0:
        raise AuthorizationRejected("Invalid revocation sequence")

    if type(minimum_sequence) is not int or minimum_sequence < 0:
        raise AuthorizationRejected("Invalid sequence floor")

    if sequence < minimum_sequence:
        raise AuthorizationRejected("Revocation rollback detected")

    for field in ("revoked_approval_ids", "revoked_signing_key_ids"):
        values = record[field]
        if (
            not isinstance(values, list)
            or any(not isinstance(v, str) or not v for v in values)
            or len(values) != len(set(values))
        ):
            raise AuthorizationRejected("Invalid revocation identifiers")

    issued = _parse_timestamp(record["issued_at"])
    expires = _parse_timestamp(record["expires_at"])
    current = now if now is not None else datetime.now(timezone.utc)

    if current.tzinfo is None:
        raise AuthorizationRejected("Revocation clock lacks timezone")

    current = current.astimezone(timezone.utc)

    if not issued <= current < expires:
        raise AuthorizationRejected("Revocation record not currently valid")

    if expires - issued > MAX_RECORD_LIFETIME:
        raise AuthorizationRejected("Revocation lifetime too long")

    return record
