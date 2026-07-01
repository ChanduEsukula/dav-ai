"""CLI entrypoint for deterministic documentation chunk ingestion.

Example:

    cd backend && python -m app.jobs.ingest_documentation_chunks --dry-run
    cd backend && python -m app.jobs.ingest_documentation_chunks --apply

This job stores allowlisted Dav AI documentation chunk metadata and
deterministic preview embedding metadata only. It does not call external
embedding APIs, create vector indexes, run semantic retrieval, produce RAG
answers, or touch product safety workflows.
"""

from __future__ import annotations

import argparse
import json
import logging

from app.services.static_docs_ingestion import ingest_documentation_chunks


logger = logging.getLogger("dav_ai.jobs.ingest_documentation_chunks")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest deterministic Dav AI documentation chunks.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Build chunks and preview embeddings without writing rows.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write documentation chunk metadata to the configured database.",
    )
    return parser.parse_args()


def execute(*, dry_run: bool = True) -> dict[str, str | int | bool | None]:
    logger.info(
        "documentation_chunk_ingestion_job_started",
        extra={
            "event": "documentation_chunk_ingestion_job_started",
            "dry_run": dry_run,
        },
    )

    summary = ingest_documentation_chunks(dry_run=dry_run).to_dict()

    logger.info(
        "documentation_chunk_ingestion_job_completed",
        extra={
            "event": "documentation_chunk_ingestion_job_completed",
            **summary,
        },
    )
    return summary


def main() -> None:
    args = parse_args()
    dry_run = not args.apply
    summary = execute(dry_run=dry_run)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
