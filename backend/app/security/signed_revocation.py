"""Verify signed revocation records without authorizing deployment."""

from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature

from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry
from app.security.validation import (
    check_signature_input,
    parse_document,
    parse_timestamp,
    utc_time,
)


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


def verify_signed_revocation(
    *,
    payload: bytes,
    signature: bytes,
    registry: TrustedKeyRegistry,
    expected_authority_id: str,
    minimum_sequence: int,
    now: datetime | None = None,
) -> dict:
    """Offline floor check only: equality is allowed; this does not consume state."""

    record = parse_document(payload, limit=65536, label="revocation",
                            duplicate="Duplicate revocation field")
    check_signature_input(signature)

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

    if sequence > 2**63 - 1:
        raise AuthorizationRejected("Invalid revocation sequence")

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

    issued = parse_timestamp(record["issued_at"])
    expires = parse_timestamp(record["expires_at"])
    current = utc_time(now if now is not None else datetime.now(timezone.utc))

    if not issued <= current < expires:
        raise AuthorizationRejected("Revocation record not currently valid")

    if expires - issued > MAX_RECORD_LIFETIME:
        raise AuthorizationRejected("Revocation lifetime too long")

    return record
