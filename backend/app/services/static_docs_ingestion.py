import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from app.db.documentation_chunks_repository import (
    DocumentationChunkStorageRecord,
    DocumentationChunkWriteResult,
    DocumentationChunksRepository,
)
from app.schemas.docs import StaticDocsChunkPreview
from app.services.static_docs_chunking import build_static_docs_chunks
from app.services.static_docs_embeddings import (
    DEFAULT_EMBEDDING_PREVIEW_VALUES,
    DeterministicFakeEmbeddingProvider,
    EmbeddingProvider,
)


logger = logging.getLogger("medtrek.static_docs_ingestion")


class DocumentationChunkStorage(Protocol):
    def save_chunks(
        self,
        records: Sequence[DocumentationChunkStorageRecord],
    ) -> list[DocumentationChunkWriteResult]:
        """Persist deterministic documentation chunk records."""


@dataclass(frozen=True)
class DocumentationChunkIngestionSummary:
    status: str
    reason: str
    attempted_count: int
    inserted_count: int
    updated_count: int
    unchanged_count: int
    skipped_count: int
    error_count: int
    embedding_provider: str | None
    embedding_model: str | None
    embedding_dimension: int | None
    dry_run: bool = False

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "status": self.status,
            "reason": self.reason,
            "attempted_count": self.attempted_count,
            "inserted_count": self.inserted_count,
            "updated_count": self.updated_count,
            "unchanged_count": self.unchanged_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "dry_run": self.dry_run,
        }


def build_documentation_chunk_storage_records(
    chunks: Sequence[StaticDocsChunkPreview],
    provider: EmbeddingProvider | None = None,
    preview_values: int = DEFAULT_EMBEDDING_PREVIEW_VALUES,
) -> list[DocumentationChunkStorageRecord]:
    embedding_provider = provider or DeterministicFakeEmbeddingProvider()
    metadata = embedding_provider.metadata
    preview_length = max(0, min(preview_values, metadata.dimension))
    records: list[DocumentationChunkStorageRecord] = []

    for chunk in chunks:
        vector = embedding_provider.embed_text(chunk.text)
        records.append(
            DocumentationChunkStorageRecord(
                chunk_id=chunk.chunk_id,
                source_path=chunk.source_path,
                title=chunk.title,
                section_heading=chunk.section_heading,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                text=chunk.text,
                character_count=chunk.character_count,
                content_hash=chunk.content_hash,
                embedding_provider=metadata.provider_name,
                embedding_model=metadata.model_name,
                embedding_dimension=metadata.dimension,
                embedding_preview=vector[:preview_length],
                embedding_status="preview",
            )
        )

    return records


def _summary_from_results(
    *,
    results: Sequence[DocumentationChunkWriteResult],
    provider: EmbeddingProvider,
    dry_run: bool = False,
) -> DocumentationChunkIngestionSummary:
    inserted_count = sum(result.status == "inserted" for result in results)
    updated_count = sum(result.status == "updated" for result in results)
    unchanged_count = sum(result.status == "unchanged" for result in results)
    skipped_count = sum(result.status == "skipped" for result in results)
    status = "completed"
    reason = "documentation_chunks_ingested"

    if dry_run:
        status = "dry_run"
        reason = "documentation_chunks_validated_without_persistence"
    elif skipped_count == len(results) and results:
        status = "skipped"
        reason = "database_not_configured"

    return DocumentationChunkIngestionSummary(
        status=status,
        reason=reason,
        attempted_count=len(results),
        inserted_count=inserted_count,
        updated_count=updated_count,
        unchanged_count=unchanged_count,
        skipped_count=skipped_count,
        error_count=0,
        embedding_provider=provider.metadata.provider_name,
        embedding_model=provider.metadata.model_name,
        embedding_dimension=provider.metadata.dimension,
        dry_run=dry_run,
    )


def ingest_documentation_chunks(
    *,
    repository: DocumentationChunkStorage | None = None,
    provider: EmbeddingProvider | None = None,
    chunks: Sequence[StaticDocsChunkPreview] | None = None,
    repo_root: Path | None = None,
    dry_run: bool = False,
) -> DocumentationChunkIngestionSummary:
    """Ingest deterministic documentation chunk metadata into storage.

    This is metadata and deterministic preview embedding ingestion only. It does
    not call external embedding APIs, create vector DB records, run semantic
    retrieval, produce generated answers, or touch safety workflows.
    """

    embedding_provider = provider or DeterministicFakeEmbeddingProvider()
    docs_chunks = list(chunks) if chunks is not None else build_static_docs_chunks(repo_root)
    records = build_documentation_chunk_storage_records(
        docs_chunks,
        provider=embedding_provider,
    )

    if dry_run:
        return _summary_from_results(
            results=[
                DocumentationChunkWriteResult(
                    chunk_id=record.chunk_id,
                    status="skipped",
                    reason="dry_run",
                )
                for record in records
            ],
            provider=embedding_provider,
            dry_run=True,
        )

    storage = repository or DocumentationChunksRepository()

    try:
        write_results = storage.save_chunks(records)
    except Exception:
        logger.exception(
            "static_docs_ingestion_failed",
            extra={"event": "static_docs_ingestion_failed"},
        )
        return DocumentationChunkIngestionSummary(
            status="error",
            reason="documentation_chunks_ingestion_failed",
            attempted_count=len(records),
            inserted_count=0,
            updated_count=0,
            unchanged_count=0,
            skipped_count=0,
            error_count=len(records),
            embedding_provider=embedding_provider.metadata.provider_name,
            embedding_model=embedding_provider.metadata.model_name,
            embedding_dimension=embedding_provider.metadata.dimension,
            dry_run=False,
        )

    return _summary_from_results(
        results=write_results,
        provider=embedding_provider,
    )
