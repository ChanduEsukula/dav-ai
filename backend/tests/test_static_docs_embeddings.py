from fastapi.testclient import TestClient

from app.main import app
from app.schemas.docs import StaticDocsChunkPreview
from app.services.static_docs_embeddings import (
    DeterministicFakeEmbeddingProvider,
    build_docs_embedding_previews,
)


client = TestClient(app)


def make_chunk(text: str = "Documentation-only source guidance.") -> StaticDocsChunkPreview:
    return StaticDocsChunkPreview(
        chunk_id="docs-test-chunk",
        source_path="docs/architecture/test.md",
        title="Test Doc",
        section_heading="Purpose",
        text=text,
        line_start=1,
        line_end=3,
        character_count=len(text),
        content_hash="abc123",
    )


def test_fake_embedding_provider_is_deterministic_for_same_text():
    provider = DeterministicFakeEmbeddingProvider(dimension=12)

    first_vector = provider.embed_text("same documentation text")
    second_vector = provider.embed_text("same documentation text")

    assert first_vector == second_vector


def test_fake_embedding_provider_changes_for_different_text():
    provider = DeterministicFakeEmbeddingProvider(dimension=12)

    first_vector = provider.embed_text("documentation source guidance")
    second_vector = provider.embed_text("different public source note")

    assert first_vector != second_vector


def test_fake_embedding_provider_returns_configured_dimension():
    provider = DeterministicFakeEmbeddingProvider(dimension=24)

    vector = provider.embed_text("dimension check")

    assert len(vector) == 24
    assert provider.metadata.dimension == 24
    assert provider.metadata.provider_name == "deterministic_fake"
    assert provider.metadata.is_test_provider is True
    assert provider.metadata.deterministic is True


def test_embedding_preview_truncates_vector_output():
    provider = DeterministicFakeEmbeddingProvider(dimension=10)

    previews = build_docs_embedding_previews(
        chunks=[make_chunk()],
        provider=provider,
        preview_values=4,
    )

    preview = previews[0]
    assert preview.chunk_id == "docs-test-chunk"
    assert preview.source_path == "docs/architecture/test.md"
    assert preview.section_heading == "Purpose"
    assert preview.embedding_dimension == 10
    assert len(preview.embedding_preview) == 4
    assert preview.content_hash == "abc123"
    assert preview.provider.provider_name == "deterministic_fake"
    assert preview.provider.dimension == 10


def test_docs_embedding_preview_route_validates_limit_and_returns_limitations():
    response = client.get(
        "/api/v1/docs/embedding-preview",
        params={"max_results": 2},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 2
    assert len(body["embeddings"]) == 2
    first_embedding = body["embeddings"][0]
    assert first_embedding["embedding_dimension"] == 16
    assert len(first_embedding["embedding_preview"]) == 6
    assert first_embedding["provider"]["provider_name"] == "deterministic_fake"
    assert first_embedding["provider"]["is_test_provider"] is True
    assert first_embedding["provider"]["deterministic"] is True
    assert "Deterministic embedding preview only" in body["limitations"][0]
    assert "not semantic search" in body["limitations"][0]
    assert "No vector database storage" in " ".join(body["limitations"])
    assert "No generated answers are produced." in body["limitations"]
    assert "Not safety advice" in " ".join(body["limitations"])

    too_small_response = client.get(
        "/api/v1/docs/embedding-preview",
        params={"max_results": 0},
    )
    assert too_small_response.status_code == 422

    too_large_response = client.get(
        "/api/v1/docs/embedding-preview",
        params={"max_results": 101},
    )
    assert too_large_response.status_code == 422


def test_existing_docs_search_and_chunks_routes_keep_response_shape():
    search_response = client.get(
        "/api/v1/docs/search",
        params={"q": "ProductScan", "max_results": 1},
    )
    chunks_response = client.get(
        "/api/v1/docs/chunks",
        params={"max_results": 1},
    )

    assert search_response.status_code == 200
    search_body = search_response.json()
    assert set(search_body.keys()) == {"query", "count", "results", "limitations"}
    assert search_body["query"] == "ProductScan"
    assert len(search_body["results"]) <= 1

    assert chunks_response.status_code == 200
    chunks_body = chunks_response.json()
    assert set(chunks_body.keys()) == {"count", "chunks", "limitations"}
    assert chunks_body["count"] == 1
    assert len(chunks_body["chunks"]) == 1
