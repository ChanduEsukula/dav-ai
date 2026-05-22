"""Schemas for public source-pull provenance metadata."""

from typing import Any

from pydantic import BaseModel


class SourcePullProvenanceItem(BaseModel):
    """Metadata-only source pull response.

    Raw public-source payloads are intentionally not exposed by this schema.
    """

    pull_id: str
    audit_id: str
    source_id: str | None = None
    source_name: str | None = None
    endpoint: str | None = None
    query: str | None = None
    query_params: dict[str, Any] | None = None
    retrieval_timestamp: str | None = None
    upstream_status: str | None = None
    record_count: int | None = None
    payload_hash: str
    transform_version: str | None = None
    created_at: str | None = None
    snapshot_id: str | None = None


class SourcePullProvenanceResponse(BaseModel):
    """Response wrapper for source-pull provenance lookups."""

    status: str
    persistence_available: bool
    item: SourcePullProvenanceItem | None = None
    message: str | None = None
