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
