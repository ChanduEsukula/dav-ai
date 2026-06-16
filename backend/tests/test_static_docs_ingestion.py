from fastapi.testclient import TestClient

from app.db.documentation_chunks_repository import (
    DocumentationChunkStorageRecord,
    DocumentationChunkWriteResult,
    DocumentationChunksRepository,
)
from app.main import app
from app.schemas.docs import StaticDocsChunkPreview
from app.services.static_docs_ingestion import (
    build_documentation_chunk_storage_records,
    ingest_documentation_chunks,
)


client = TestClient(app)


def make_chunk(
    *,
    chunk_id: str = "docs-test-chunk",
    text: str = "Documentation-only source guidance.",
    content_hash: str = "hash-one",
) -> StaticDocsChunkPreview:
    return StaticDocsChunkPreview(
        chunk_id=chunk_id,
        source_path="docs/architecture/test.md",
        title="Test Doc",
        section_heading="Purpose",
        text=text,
        line_start=1,
        line_end=3,
        character_count=len(text),
        content_hash=content_hash,
    )


class FakeDocumentationChunksRepository:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.rows: dict[str, DocumentationChunkStorageRecord] = {}
        self.save_calls = 0

    def save_chunks(
        self,
        records: list[DocumentationChunkStorageRecord],
    ) -> list[DocumentationChunkWriteResult]:
        self.save_calls += 1

        if self.fail:
            raise RuntimeError("database unavailable")

        results: list[DocumentationChunkWriteResult] = []
        for record in records:
            existing = self.rows.get(record.chunk_id)
            if existing is None:
                self.rows[record.chunk_id] = record
                results.append(
                    DocumentationChunkWriteResult(
                        chunk_id=record.chunk_id,
                        status="inserted",
                    )
                )
                continue

            if existing.content_hash == record.content_hash:
                results.append(
                    DocumentationChunkWriteResult(
                        chunk_id=record.chunk_id,
                        status="unchanged",
                    )
                )
                continue

            self.rows[record.chunk_id] = record
            results.append(
                DocumentationChunkWriteResult(
                    chunk_id=record.chunk_id,
                    status="updated",
                )
            )

        return results


def test_first_documentation_chunk_ingestion_inserts_chunks():
    repository = FakeDocumentationChunksRepository()
    chunks = [
        make_chunk(chunk_id="docs-one", content_hash="hash-one"),
        make_chunk(chunk_id="docs-two", content_hash="hash-two"),
    ]

    summary = ingest_documentation_chunks(repository=repository, chunks=chunks)

    assert summary.status == "completed"
    assert summary.attempted_count == 2
    assert summary.inserted_count == 2
    assert summary.updated_count == 0
    assert summary.unchanged_count == 0
    assert summary.error_count == 0
    assert set(repository.rows) == {"docs-one", "docs-two"}


def test_second_documentation_chunk_ingestion_is_idempotent_for_same_hashes():
    repository = FakeDocumentationChunksRepository()
    chunks = [make_chunk(chunk_id="docs-one", content_hash="hash-one")]

    first_summary = ingest_documentation_chunks(repository=repository, chunks=chunks)
    second_summary = ingest_documentation_chunks(repository=repository, chunks=chunks)

    assert first_summary.inserted_count == 1
    assert second_summary.status == "completed"
    assert second_summary.inserted_count == 0
    assert second_summary.updated_count == 0
    assert second_summary.unchanged_count == 1
    assert repository.save_calls == 2


def test_changed_documentation_chunk_content_hash_updates_existing_row():
    repository = FakeDocumentationChunksRepository()
    original_chunk = make_chunk(
        chunk_id="docs-one",
        text="Original documentation text.",
        content_hash="hash-one",
    )
    changed_chunk = make_chunk(
        chunk_id="docs-one",
        text="Changed documentation text.",
        content_hash="hash-two",
    )

    ingest_documentation_chunks(repository=repository, chunks=[original_chunk])
    summary = ingest_documentation_chunks(repository=repository, chunks=[changed_chunk])

    assert summary.inserted_count == 0
    assert summary.updated_count == 1
    assert summary.unchanged_count == 0
    assert repository.rows["docs-one"].content_hash == "hash-two"
    assert repository.rows["docs-one"].text == "Changed documentation text."


def test_preview_embedding_metadata_is_stored_with_deterministic_fake_provider():
    chunk = make_chunk()

    records = build_documentation_chunk_storage_records([chunk])

    assert len(records) == 1
    record = records[0]
    assert record.embedding_provider == "deterministic_fake"
    assert record.embedding_model == "deterministic-fake-docs-embedding-v1"
    assert record.embedding_dimension == 16
    assert record.embedding_preview is not None
    assert len(record.embedding_preview) == 6
    assert record.embedding_status == "preview"


def test_ingestion_uses_local_fake_embeddings_without_external_provider_metadata():
    repository = FakeDocumentationChunksRepository()

    summary = ingest_documentation_chunks(
        repository=repository,
        chunks=[make_chunk()],
    )

    stored_record = repository.rows["docs-test-chunk"]
    assert summary.embedding_provider == "deterministic_fake"
    assert summary.embedding_model == "deterministic-fake-docs-embedding-v1"
    assert "openai" not in stored_record.embedding_provider.lower()
    assert stored_record.embedding_preview == build_documentation_chunk_storage_records(
        [make_chunk()]
    )[0].embedding_preview


def test_documentation_chunks_repository_skips_when_database_not_configured():
    repository = DocumentationChunksRepository()
    record = build_documentation_chunk_storage_records([make_chunk()])[0]

    results = repository.save_chunks([record])

    assert results == [
        DocumentationChunkWriteResult(
            chunk_id="docs-test-chunk",
            status="skipped",
            reason="database_not_configured",
        )
    ]


def test_ingestion_errors_fail_softly_and_docs_search_still_works():
    repository = FakeDocumentationChunksRepository(fail=True)

    summary = ingest_documentation_chunks(
        repository=repository,
        chunks=[make_chunk()],
    )

    assert summary.status == "error"
    assert summary.reason == "documentation_chunks_ingestion_failed"
    assert summary.error_count == 1

    response = client.get(
        "/api/v1/docs/search",
        params={"q": "ProductScan", "max_results": 1},
    )
    assert response.status_code == 200
    assert set(response.json().keys()) == {"query", "count", "results", "limitations"}


def test_dry_run_builds_records_without_calling_repository():
    repository = FakeDocumentationChunksRepository()

    summary = ingest_documentation_chunks(
        repository=repository,
        chunks=[make_chunk()],
        dry_run=True,
    )

    assert summary.status == "dry_run"
    assert summary.reason == "documentation_chunks_validated_without_persistence"
    assert summary.attempted_count == 1
    assert summary.skipped_count == 1
    assert summary.dry_run is True
    assert repository.save_calls == 0
