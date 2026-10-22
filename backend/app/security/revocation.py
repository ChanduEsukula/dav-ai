"""Offline revocation checks. Not a deployment authorization gate."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.security.staging_authorization import AuthorizationRejected


MAX_REVOCATION_AGE = timedelta(minutes=5)


@dataclass(frozen=True)
class RevocationSnapshot:
    fetched_at: datetime
    revoked_approval_ids: frozenset[str]


def check_revocation(
    approval_id: str,
    snapshot: RevocationSnapshot | None,
    *,
    now: datetime | None = None,
) -> None:
    """Reject missing, stale, future, or revoked approval state."""

    if not isinstance(approval_id, str) or not approval_id:
        raise AuthorizationRejected("Invalid approval identifier")

    if snapshot is None:
        raise AuthorizationRejected("Revocation state unavailable")

    current = now if now is not None else datetime.now(timezone.utc)

    if current.tzinfo is None or snapshot.fetched_at.tzinfo is None:
        raise AuthorizationRejected("Revocation clock lacks timezone")

    age = current.astimezone(timezone.utc) - snapshot.fetched_at.astimezone(timezone.utc)

    if age < timedelta(0) or age > MAX_REVOCATION_AGE:
        raise AuthorizationRejected("Revocation state is not fresh")

    if approval_id in snapshot.revoked_approval_ids:
        raise AuthorizationRejected("Authorization revoked")
