from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from app.schemas.docs import (
    DocsEmbeddingProviderMetadata,
    StaticDocsChunkPreview,
    StaticDocsEmbeddingPreview,
)
from app.services.static_docs_chunking import (
    MAX_CHUNK_PREVIEW_RESULTS,
    preview_static_docs_chunks,
)


DOCS_EMBEDDING_PREVIEW_LIMITATIONS = [
    "Deterministic embedding preview only. This is not semantic search.",
    "No vector database storage, pgvector migration, external embedding API, or LLM call is used.",
    "No generated answers are produced.",
    "Not safety advice and not a safety determination for any product, drug, food, supplement, or cosmetic.",
    "Verify official FDA/USDA sources before acting.",
]

DEFAULT_FAKE_EMBEDDING_DIMENSION = 16
DEFAULT_EMBEDDING_PREVIEW_VALUES = 6


@dataclass(frozen=True)
class EmbeddingProviderMetadata:
    provider_name: str
    dimension: int
    model_name: str | None = None
    is_test_provider: bool = True
    deterministic: bool = True


class EmbeddingProvider(Protocol):
    @property
    def metadata(self) -> EmbeddingProviderMetadata:
        """Return provider identity and vector metadata."""

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for the provided text."""


class DeterministicFakeEmbeddingProvider:
    """Preview-only deterministic provider; it never calls external services."""

    def __init__(
        self,
        dimension: int = DEFAULT_FAKE_EMBEDDING_DIMENSION,
        model_name: str = "deterministic-fake-docs-embedding-v1",
    ) -> None:
        self._metadata = EmbeddingProviderMetadata(
            provider_name="deterministic_fake",
            dimension=max(1, dimension),
            model_name=model_name,
            is_test_provider=True,
            deterministic=True,
        )

    @property
    def metadata(self) -> EmbeddingProviderMetadata:
        return self._metadata

    def embed_text(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0

        while len(values) < self.metadata.dimension:
            digest = sha256(f"{counter}:{text}".encode("utf-8")).digest()
            for offset in range(0, len(digest), 4):
                if len(values) >= self.metadata.dimension:
                    break

                raw_value = int.from_bytes(digest[offset:offset + 4], "big")
                normalized = (raw_value / 0xFFFFFFFF) * 2 - 1
                values.append(round(normalized, 6))

            counter += 1

        return values


def _schema_provider_metadata(
    metadata: EmbeddingProviderMetadata,
) -> DocsEmbeddingProviderMetadata:
    return DocsEmbeddingProviderMetadata(
        provider_name=metadata.provider_name,
        dimension=metadata.dimension,
        model_name=metadata.model_name,
        is_test_provider=metadata.is_test_provider,
        deterministic=metadata.deterministic,
    )


def build_docs_embedding_previews(
    chunks: list[StaticDocsChunkPreview],
    provider: EmbeddingProvider | None = None,
    preview_values: int = DEFAULT_EMBEDDING_PREVIEW_VALUES,
) -> list[StaticDocsEmbeddingPreview]:
    embedding_provider = provider or DeterministicFakeEmbeddingProvider()
    metadata = embedding_provider.metadata
    provider_metadata = _schema_provider_metadata(metadata)
    preview_length = max(0, min(preview_values, metadata.dimension))
    previews: list[StaticDocsEmbeddingPreview] = []

    for chunk in chunks:
        vector = embedding_provider.embed_text(chunk.text)
        previews.append(
            StaticDocsEmbeddingPreview(
                chunk_id=chunk.chunk_id,
                source_path=chunk.source_path,
                section_heading=chunk.section_heading,
                embedding_dimension=metadata.dimension,
                embedding_preview=vector[:preview_length],
                content_hash=chunk.content_hash,
                provider=provider_metadata,
            )
        )

    return previews


def preview_static_docs_embeddings(
    max_results: int = 20,
    provider: EmbeddingProvider | None = None,
) -> list[StaticDocsEmbeddingPreview]:
    bounded_limit = max(1, min(max_results, MAX_CHUNK_PREVIEW_RESULTS))
    chunks = preview_static_docs_chunks(max_results=bounded_limit)
    return build_docs_embedding_previews(chunks=chunks, provider=provider)
