from fastapi.testclient import TestClient

from app.db.documentation_chunks_repository import (
    DocumentationChunkSemanticCandidate,
    DocumentationChunksRepository,
)
from app.main import app
from app.services.static_docs_embeddings import DeterministicFakeEmbeddingProvider
from app.services.static_docs_semantic_preview import (
    semantic_preview_search,
)


client = TestClient(app)


class FakeSemanticPreviewRepository:
    def __init__(self, candidates: list[DocumentationChunkSemanticCandidate]) -> None:
        self.candidates = candidates
        self.requested_limits: list[int] = []

    def list_semantic_preview_candidates(
        self,
        *,
        limit: int = 200,
    ) -> list[DocumentationChunkSemanticCandidate]:
        self.requested_limits.append(limit)
        return self.candidates[:limit]


def make_candidate(
    *,
    chunk_id: str,
    text: str,
    embedding_text: str,
    source_path: str = "docs/architecture/test.md",
) -> DocumentationChunkSemanticCandidate:
    provider = DeterministicFakeEmbeddingProvider()
    return DocumentationChunkSemanticCandidate(
        chunk_id=chunk_id,
        source_path=source_path,
        title="Test Doc",
        section_heading="Purpose",
        text=text,
        line_start=1,
        line_end=3,
        content_hash=f"hash-{chunk_id}",
        embedding_provider=provider.metadata.provider_name,
        embedding_model=provider.metadata.model_name,
        embedding_dimension=provider.metadata.dimension,
        embedding_preview=provider.embed_text(embedding_text)[:6],
    )


def test_semantic_preview_ranks_results_with_deterministic_fake_vectors():
    repository = FakeSemanticPreviewRepository(
        [
            make_candidate(
                chunk_id="docs-low",
                text="Unrelated operational note.",
                embedding_text="distant unrelated text",
            ),
            make_candidate(
                chunk_id="docs-high",
                text="Source guidance explains official records.",
                embedding_text="source guidance",
            ),
        ]
    )

    results = semantic_preview_search(
        "source guidance",
        repository=repository,
        max_results=2,
    )

    assert [result.chunk_id for result in results] == ["docs-high", "docs-low"]
    assert results[0].similarity_score >= results[1].similarity_score
    assert results[0].snippet == "Source guidance explains official records."
    assert results[0].embedding_provider == "deterministic_fake"
    assert "openai" not in (results[0].embedding_model or "").lower()


def test_semantic_preview_respects_max_results_limit():
    repository = FakeSemanticPreviewRepository(
        [
            make_candidate(
                chunk_id=f"docs-{index}",
                text=f"Documentation chunk {index}",
                embedding_text=f"Documentation chunk {index}",
                source_path=f"docs/architecture/{index}.md",
            )
            for index in range(5)
        ]
    )

    results = semantic_preview_search(
        "documentation",
        repository=repository,
        max_results=3,
    )

    assert len(results) == 3
    assert repository.requested_limits == [200]


def test_semantic_preview_repository_returns_empty_when_database_url_missing():
    repository = DocumentationChunksRepository()

    assert repository.list_semantic_preview_candidates() == []


def test_docs_semantic_preview_route_validates_query_and_max_results():
    short_response = client.get(
        "/api/v1/docs/semantic-preview",
        params={"q": "x"},
    )
    assert short_response.status_code == 422

    blankish_response = client.get(
        "/api/v1/docs/semantic-preview",
        params={"q": " x "},
    )
    assert blankish_response.status_code == 400
    assert (
        blankish_response.json()["detail"]["code"]
        == "DOCS_SEMANTIC_PREVIEW_QUERY_TOO_SHORT"
    )

    too_many_response = client.get(
        "/api/v1/docs/semantic-preview",
        params={"q": "source guidance", "max_results": 21},
    )
    assert too_many_response.status_code == 422


def test_docs_semantic_preview_route_handles_missing_database_gracefully():
    response = client.get(
        "/api/v1/docs/semantic-preview",
        params={"q": "source guidance", "max_results": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "source guidance"
    assert body["count"] == 0
    assert body["results"] == []
    assert "answer" not in body
    assert "generated_answer" not in body


def test_docs_semantic_preview_route_includes_limitations():
    response = client.get(
        "/api/v1/docs/semantic-preview",
        params={"q": "source guidance", "max_results": 1},
    )

    assert response.status_code == 200
    limitations = response.json()["limitations"]

    assert "Deterministic semantic retrieval preview only" in limitations[0]
    assert "not production semantic search" in limitations[0]
    assert "No pgvector" in " ".join(limitations)
    assert "No generated answers are produced." in limitations
    assert "Not safety advice" in " ".join(limitations)
    assert "Official FDA/USDA/source workflows remain authoritative." in limitations


def test_existing_docs_routes_keep_response_shape():
    search_response = client.get(
        "/api/v1/docs/search",
        params={"q": "ProductScan", "max_results": 1},
    )
    chunks_response = client.get(
        "/api/v1/docs/chunks",
        params={"max_results": 1},
    )
    embeddings_response = client.get(
        "/api/v1/docs/embedding-preview",
        params={"max_results": 1},
    )

    assert search_response.status_code == 200
    assert set(search_response.json()) == {"query", "count", "results", "limitations"}

    assert chunks_response.status_code == 200
    assert set(chunks_response.json()) == {"count", "chunks", "limitations"}

    assert embeddings_response.status_code == 200
    assert set(embeddings_response.json()) == {"count", "embeddings", "limitations"}
