from pydantic import BaseModel


class StaticDocsSearchResult(BaseModel):
    title: str
    source_path: str
    section_heading: str | None = None
    snippet: str
    matched_terms: list[str]
    line_start: int
    line_end: int


class StaticDocsSearchResponse(BaseModel):
    query: str
    count: int
    results: list[StaticDocsSearchResult]
    limitations: list[str]


class StaticDocsChunkPreview(BaseModel):
    chunk_id: str
    source_path: str
    title: str
    section_heading: str | None = None
    text: str
    line_start: int
    line_end: int
    character_count: int
    content_hash: str


class StaticDocsChunkPreviewResponse(BaseModel):
    count: int
    chunks: list[StaticDocsChunkPreview]
    limitations: list[str]


class DocsEmbeddingProviderMetadata(BaseModel):
    provider_name: str
    dimension: int
    model_name: str | None = None
    is_test_provider: bool
    deterministic: bool


class StaticDocsEmbeddingPreview(BaseModel):
    chunk_id: str
    source_path: str
    section_heading: str | None = None
    embedding_dimension: int
    embedding_preview: list[float]
    content_hash: str
    provider: DocsEmbeddingProviderMetadata


class StaticDocsEmbeddingPreviewResponse(BaseModel):
    count: int
    embeddings: list[StaticDocsEmbeddingPreview]
    limitations: list[str]


class StaticDocsSemanticPreviewResult(BaseModel):
    chunk_id: str
    source_path: str
    title: str
    section_heading: str | None = None
    snippet: str
    line_start: int
    line_end: int
    content_hash: str
    similarity_score: float
    embedding_provider: str | None = None
    embedding_model: str | None = None


class StaticDocsSemanticPreviewResponse(BaseModel):
    query: str
    count: int
    results: list[StaticDocsSemanticPreviewResult]
    limitations: list[str]
