"""Tests for the scheduled saved monitor refresh CLI job."""

import pytest

from app.jobs import run_due_saved_monitors


def test_clamp_limit_uses_minimum_for_low_values():
    assert run_due_saved_monitors.clamp_limit(0) == 1
    assert run_due_saved_monitors.clamp_limit(-10) == 1


def test_clamp_limit_preserves_valid_values():
    assert run_due_saved_monitors.clamp_limit(1) == 1
    assert run_due_saved_monitors.clamp_limit(10) == 10
    assert run_due_saved_monitors.clamp_limit(50) == 50


def test_clamp_limit_uses_maximum_for_high_values():
    assert run_due_saved_monitors.clamp_limit(51) == 50
    assert run_due_saved_monitors.clamp_limit(500) == 50


@pytest.mark.anyio
async def test_execute_adds_requested_and_safe_limits(monkeypatch):
    async def fake_run_due_saved_monitors(*, limit: int):
        return {
            "status": "ok",
            "job_started_at": "2026-05-15T00:00:00+00:00",
            "due_count": 0,
            "attempted_count": 0,
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "run_ids": [],
            "observed_limit": limit,
        }

    monkeypatch.setattr(
        run_due_saved_monitors,
        "run_due_saved_monitors",
        fake_run_due_saved_monitors,
    )

    summary = await run_due_saved_monitors.execute(limit=500)

    assert summary["status"] == "ok"
    assert summary["requested_limit"] == 500
    assert summary["safe_limit"] == 50
    assert summary["observed_limit"] == 50
