"""Offline revocation checks. Not a deployment authorization gate."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.security.staging_authorization import AuthorizationRejected
from app.security.validation import utc_time


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

    if not isinstance(snapshot, RevocationSnapshot):
        raise AuthorizationRejected("Revocation state unavailable")
    if (type(snapshot.revoked_approval_ids) is not frozenset
            or any(type(v) is not str or not v for v in snapshot.revoked_approval_ids)):
        raise AuthorizationRejected("Invalid revocation identifiers")
    current = utc_time(now if now is not None else datetime.now(timezone.utc))
    age = current - utc_time(snapshot.fetched_at)

    if age < timedelta(0) or age > MAX_REVOCATION_AGE:
        raise AuthorizationRejected("Revocation state is not fresh")

    if approval_id in snapshot.revoked_approval_ids:
        raise AuthorizationRejected("Authorization revoked")
