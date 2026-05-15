"""CLI entrypoint for scheduled saved monitor refresh.

Intended future Render Cron command:

    cd backend && python -m app.jobs.run_due_saved_monitors

This job does not send alerts. It only runs due saved monitors and records
run-history rows.
"""

from __future__ import annotations

import argparse
import asyncio
import json

from app.services.scheduled_monitor_refresh import run_due_saved_monitors


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Run due saved monitors.")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of due monitors to run in one job.",
    )
    return parser.parse_args()


async def main() -> None:
    """Run due saved monitors and print a JSON summary."""

    args = parse_args()
    summary = await run_due_saved_monitors(limit=args.limit)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
