"""CLI entrypoint for scheduled saved monitor refresh.

Intended future Render Cron command:

    cd backend && python -m app.jobs.run_due_saved_monitors --limit 10

This job does not send alerts. It only runs due saved monitors and records
run-history rows.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any

from app.services.scheduled_monitor_refresh import run_due_saved_monitors

logger = logging.getLogger("dav_ai.jobs.run_due_saved_monitors")

DEFAULT_LIMIT = 10
MIN_LIMIT = 1
MAX_LIMIT = 50


def clamp_limit(limit: int) -> int:
    """Clamp a requested job limit into a safe execution range."""

    return max(MIN_LIMIT, min(limit, MAX_LIMIT))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Run due saved monitors.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum number of due monitors to run in one job. Clamped to {MIN_LIMIT}-{MAX_LIMIT}.",
    )
    return parser.parse_args()


async def execute(limit: int) -> dict[str, Any]:
    """Run due saved monitors with safe limit handling."""

    safe_limit = clamp_limit(limit)

    logger.info(
        "scheduled_saved_monitor_job_started",
        extra={
            "event": "scheduled_saved_monitor_job_started",
            "requested_limit": limit,
            "safe_limit": safe_limit,
        },
    )

    summary = await run_due_saved_monitors(limit=safe_limit)
    summary["requested_limit"] = limit
    summary["safe_limit"] = safe_limit

    logger.info(
        "scheduled_saved_monitor_job_completed",
        extra={
            "event": "scheduled_saved_monitor_job_completed",
            "requested_limit": limit,
            "safe_limit": safe_limit,
            "due_count": summary.get("due_count"),
            "attempted_count": summary.get("attempted_count"),
            "success_count": summary.get("success_count"),
            "error_count": summary.get("error_count"),
        },
    )

    return summary


async def main() -> None:
    """Run due saved monitors and print a JSON summary."""

    args = parse_args()
    summary = await execute(limit=args.limit)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())