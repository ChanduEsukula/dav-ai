"""Isolated policy/state primitives. No provider or hosted serving integration.

Policy and StateStore are TRUSTED inputs, never request/document parameters.
Implementations must enforce the StateStore contract outside the app's rollback domain.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.security.signed_revocation import verify_signed_revocation
from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry, verify_with_trusted_keys
from app.security.validation import parse_timestamp, utc_time


@dataclass(frozen=True)
class LifecycleKey:
    public_key: Ed25519PublicKey
    not_before: datetime
    not_after: datetime
    revoked: bool = False

    def __post_init__(self):
        if not isinstance(self.public_key, Ed25519PublicKey) or type(self.revoked) is not bool:
            raise ValueError("Invalid lifecycle key")
        object.__setattr__(self, "not_before", utc_time(self.not_before))
        object.__setattr__(self, "not_after", utc_time(self.not_after))
        if self.not_before >= self.not_after:
            raise ValueError("Invalid key validity interval")

    def check(self, issued: datetime, expires: datetime, current: datetime) -> None:
        if self.revoked:
            raise AuthorizationRejected("Signing key revoked by trusted policy")
        if not self.not_before <= issued < expires <= self.not_after:
            raise AuthorizationRejected("Document outside signing key validity interval")
        if not self.not_before <= current < self.not_after:
            raise AuthorizationRejected("Signing key not currently active")


@dataclass(frozen=True)
class TrustPolicy:
    authority_id: str
    release_id: str
    database_sha256: str
    deployment_id: str
    approval_keys: Mapping[str, LifecycleKey]
    revocation_keys: Mapping[str, LifecycleKey]

    def __post_init__(self):
        for value in (self.authority_id, self.release_id, self.deployment_id):
            if type(value) is not str or not value.strip():
                raise ValueError("Missing trusted scope")
        if not isinstance(self.database_sha256, str) or not re.fullmatch("[0-9a-f]{64}", self.database_sha256):
            raise ValueError("Invalid trusted SHA256")
        for field in ("approval_keys", "revocation_keys"):
            keys = dict(getattr(self, field))
            if not keys or any(type(k) is not str or not k or not isinstance(v, LifecycleKey)
                               for k, v in keys.items()):
                raise ValueError("Invalid trusted lifecycle registry")
            material = [v.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
                        for v in keys.values()]
            if len(material) != len(set(material)):
                raise ValueError("Signing key aliases are not permitted")
            object.__setattr__(self, field, MappingProxyType(keys))
        if set(self.approval_keys) & set(self.revocation_keys):
            raise ValueError("Signing key roles must be separate")
        approval_bytes = {v.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
                          for v in self.approval_keys.values()}
        if any(v.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw) in approval_bytes
               for v in self.revocation_keys.values()):
            raise ValueError("Signing key material must be separate by role")


@dataclass(frozen=True)
class RevocationCheckpoint:
    authority_id: str
    sequence_number: int
    payload: bytes = b""
    signature: bytes = b""
    revoked_approval_ids: frozenset[str] = frozenset()
    revoked_signing_key_ids: frozenset[str] = frozenset()

    def __post_init__(self):
        if (type(self.authority_id) is not str or not self.authority_id
                or type(self.sequence_number) is not int
                or not 0 <= self.sequence_number <= 2**63 - 1
                or type(self.payload) is not bytes or type(self.signature) is not bytes
                or any(type(values) is not frozenset or any(type(v) is not str or not v for v in values)
                       for values in (self.revoked_approval_ids, self.revoked_signing_key_ids))):
            raise ValueError("Invalid trusted checkpoint")


class StateStore(Protocol):
    """Trusted, linearizable, durable store; outage/corruption must raise.

    read must detect rollback across restarts/restores, not merely return a local
    file. Missing state MUST NOT initialize a sequence floor. Bootstrap/recovery
    requires an independent authenticated checkpoint and cumulative revocations.
    CAS must compare the ENTIRE checkpoint and durably commit before returning
    True. False means conflict. Ambiguous commit errors deny; reread to recover.
    """

    def read(self, authority_id: str) -> RevocationCheckpoint | None: ...

    def compare_and_swap(self, authority_id: str, expected: RevocationCheckpoint,
                         replacement: RevocationCheckpoint) -> bool: ...


def _read(store: StateStore, policy: TrustPolicy) -> RevocationCheckpoint:
    try:
        checkpoint = store.read(policy.authority_id)
    except Exception as exc:
        raise AuthorizationRejected("Trusted state unavailable") from exc
    if not isinstance(checkpoint, RevocationCheckpoint) or checkpoint.authority_id != policy.authority_id:
        raise AuthorizationRejected("Trusted state missing or wrong authority")
    return checkpoint


def _record(payload: bytes, signature: bytes, policy: TrustPolicy, floor: int,
            current: datetime) -> dict:
    record = verify_signed_revocation(
        payload=payload, signature=signature,
        registry=TrustedKeyRegistry({k: v.public_key for k, v in policy.revocation_keys.items()}),
        expected_authority_id=policy.authority_id, minimum_sequence=floor, now=current,
    )
    policy.revocation_keys[record["key_id"]].check(
        parse_timestamp(record["issued_at"]), parse_timestamp(record["expires_at"]), current,
    )
    return record


def accept_signed_revocation(*, payload: bytes, signature: bytes, policy: TrustPolicy,
                             store: StateStore, now: datetime | None = None) -> RevocationCheckpoint:
    """Consume a strictly newer cumulative record using atomic trusted state.

    Re-delivery (including identical bytes) is rejected; it cannot renew freshness.
    A cached accepted record is read, not ingested again, for each decision.
    """
    current = utc_time(now if now is not None else datetime.now(timezone.utc))
    previous = _read(store, policy)
    record = _record(payload, signature, policy, previous.sequence_number + 1, current)
    approvals = frozenset(record["revoked_approval_ids"])
    keys = frozenset(record["revoked_signing_key_ids"])
    if not previous.revoked_approval_ids <= approvals or not previous.revoked_signing_key_ids <= keys:
        raise AuthorizationRejected("Cumulative revocations cannot be removed")
    replacement = RevocationCheckpoint(policy.authority_id, record["sequence_number"],
                                       payload, signature, approvals, keys)
    try:
        committed = store.compare_and_swap(policy.authority_id, previous, replacement)
    except Exception as exc:
        raise AuthorizationRejected("Trusted state commit unavailable") from exc
    if committed is not True:
        raise AuthorizationRejected("Trusted state changed concurrently")
    return replacement


def validate_trusted_staging_decision(*, payload: bytes, signature: bytes, policy: TrustPolicy,
                                      store: StateStore, now: datetime | None = None) -> dict:
    """Offline decision only; success is not a reusable serving capability.

    No caller-provided key, sequence floor, scope or unsigned snapshot is accepted.
    Policy/store themselves still require independently trusted provisioning.
    """
    current = utc_time(now if now is not None else datetime.now(timezone.utc))
    checkpoint = _read(store, policy)
    record = _record(checkpoint.payload, checkpoint.signature, policy, checkpoint.sequence_number, current)
    if (record["sequence_number"] != checkpoint.sequence_number
            or frozenset(record["revoked_approval_ids"]) != checkpoint.revoked_approval_ids
            or frozenset(record["revoked_signing_key_ids"]) != checkpoint.revoked_signing_key_ids):
        raise AuthorizationRejected("Trusted state inconsistent")
    claims = verify_with_trusted_keys(
        payload=payload, signature=signature,
        registry=TrustedKeyRegistry({k: v.public_key for k, v in policy.approval_keys.items()}),
        expected_release_id=policy.release_id, expected_database_sha256=policy.database_sha256,
        expected_deployment_id=policy.deployment_id, now=current,
    )
    policy.approval_keys[claims["key_id"]].check(
        parse_timestamp(claims["issued_at"]), parse_timestamp(claims["expires_at"]), current,
    )
    if claims["approval_id"] in checkpoint.revoked_approval_ids:
        raise AuthorizationRejected("Approval has been revoked")
    if claims["key_id"] in checkpoint.revoked_signing_key_ids:
        raise AuthorizationRejected("Approval signing key has been revoked")
    if _read(store, policy) != checkpoint:
        raise AuthorizationRejected("Trusted state changed during decision")
    return claims
