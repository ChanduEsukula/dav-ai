from dataclasses import dataclass
from pathlib import Path
import re

from app.schemas.docs import StaticDocsSearchResult


DOCS_SEARCH_LIMITATIONS = [
    "Documentation search only. Results are snippets from Dav AI repository documentation.",
    "Not medical advice.",
    "Not a safety determination for any product, drug, food, supplement, or cosmetic.",
    "Verify official FDA/USDA sources before acting.",
]

MAX_SNIPPET_RESULTS = 20
DEFAULT_SNIPPET_CONTEXT_LINES = 1


@dataclass(frozen=True)
class SearchableDoc:
    path: Path
    source_path: str


@dataclass(frozen=True)
class CandidateMatch:
    result: StaticDocsSearchResult
    score: int
    first_line: int


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_allowed_doc_paths(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or get_repo_root()
    candidates: list[Path] = []

    exact_files = [
        root / "README.md",
        root / "docs" / "operations_runbook.md",
    ]
    for path in exact_files:
        if path.is_file():
            candidates.append(path.resolve())

    for pattern in [
        root / "docs" / "architecture",
        root / "docs" / "demo",
        root / "docs" / "productscan",
    ]:
        if pattern.is_dir():
            candidates.extend(path.resolve() for path in pattern.glob("*.md") if path.is_file())

    return sorted(set(candidates), key=lambda path: path.relative_to(root).as_posix())


def get_searchable_docs(repo_root: Path | None = None) -> list[SearchableDoc]:
    root = repo_root or get_repo_root()
    docs: list[SearchableDoc] = []

    for path in get_allowed_doc_paths(root):
        try:
            relative_path = path.relative_to(root).as_posix()
        except ValueError:
            continue

        docs.append(SearchableDoc(path=path, source_path=relative_path))

    return docs


def tokenize_query(query: str) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []

    for term in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", query.lower()):
        if len(term) < 2 or term in seen:
            continue
        seen.add(term)
        terms.append(term)

    return terms


def _line_terms(line: str, query_terms: list[str]) -> list[str]:
    normalized_line = line.lower()
    return [term for term in query_terms if term in normalized_line]


def _extract_title(lines: list[str], fallback: str) -> str:
    for line in lines:
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback


def _heading_for_line(lines: list[str], line_index: int) -> str | None:
    for index in range(line_index, -1, -1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", lines[index])
        if match:
            return match.group(2).strip()
    return None


def _build_snippet(lines: list[str], line_index: int, context_lines: int) -> tuple[str, int, int]:
    start_index = max(0, line_index - context_lines)
    end_index = min(len(lines), line_index + context_lines + 1)
    snippet_lines = [
        line.strip()
        for line in lines[start_index:end_index]
        if line.strip()
    ]
    snippet = " ".join(snippet_lines)
    return snippet, start_index + 1, end_index


def _score_match(matched_terms: list[str], line: str, line_index: int) -> int:
    heading_bonus = 3 if re.match(r"^#{1,6}\s+", line) else 0
    early_bonus = max(0, 5 - min(line_index, 5))
    return len(matched_terms) * 10 + heading_bonus + early_bonus


def search_static_docs(
    query: str,
    max_results: int = 8,
    repo_root: Path | None = None,
) -> list[StaticDocsSearchResult]:
    clean_query = query.strip()
    query_terms = tokenize_query(clean_query)
    if not query_terms:
        return []

    bounded_limit = max(1, min(max_results, MAX_SNIPPET_RESULTS))
    matches: list[CandidateMatch] = []

    for doc in get_searchable_docs(repo_root):
        text = doc.path.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = _extract_title(lines, fallback=doc.path.stem.replace("_", " ").title())
        seen_snippets: set[tuple[int, int]] = set()

        for index, line in enumerate(lines):
            matched_terms = _line_terms(line, query_terms)
            if not matched_terms:
                continue

            snippet, line_start, line_end = _build_snippet(
                lines,
                index,
                DEFAULT_SNIPPET_CONTEXT_LINES,
            )
            snippet_key = (line_start, line_end)
            if snippet_key in seen_snippets:
                continue
            seen_snippets.add(snippet_key)

            snippet_terms = _line_terms(snippet, query_terms)
            result = StaticDocsSearchResult(
                title=title,
                source_path=doc.source_path,
                section_heading=_heading_for_line(lines, index),
                snippet=snippet,
                matched_terms=snippet_terms,
                line_start=line_start,
                line_end=line_end,
            )
            matches.append(
                CandidateMatch(
                    result=result,
                    score=_score_match(matched_terms, line, index),
                    first_line=line_start,
                )
            )

    matches.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.result.source_path,
            candidate.first_line,
        )
    )

    return [candidate.result for candidate in matches[:bounded_limit]]
