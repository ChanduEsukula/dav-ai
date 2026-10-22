from datetime import datetime, timedelta, timezone

import pytest

from app.security.revocation import (
    RevocationSnapshot,
    check_revocation,
)
from app.security.staging_authorization import AuthorizationRejected


NOW = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)


def snapshot(*revoked, age=timedelta(minutes=1)):
    return RevocationSnapshot(
        fetched_at=NOW - age,
        revoked_approval_ids=frozenset(revoked),
    )


def test_active_approval_accepted():
    check_revocation("approval-001", snapshot(), now=NOW)


def test_revoked_approval_rejected():
    with pytest.raises(AuthorizationRejected, match="revoked"):
        check_revocation(
            "approval-001",
            snapshot("approval-001"),
            now=NOW,
        )


def test_missing_revocation_state_rejected():
    with pytest.raises(AuthorizationRejected, match="unavailable"):
        check_revocation("approval-001", None, now=NOW)


def test_stale_revocation_state_rejected():
    with pytest.raises(AuthorizationRejected, match="not fresh"):
        check_revocation(
            "approval-001",
            snapshot(age=timedelta(minutes=6)),
            now=NOW,
        )


def test_future_revocation_state_rejected():
    with pytest.raises(AuthorizationRejected, match="not fresh"):
        check_revocation(
            "approval-001",
            snapshot(age=timedelta(minutes=-1)),
            now=NOW,
        )


def test_empty_approval_id_rejected():
    with pytest.raises(AuthorizationRejected):
        check_revocation("", snapshot(), now=NOW)
