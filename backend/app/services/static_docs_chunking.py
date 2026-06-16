from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

from app.schemas.docs import StaticDocsChunkPreview
from app.services.static_docs_retrieval import get_searchable_docs


DOCS_CHUNK_LIMITATIONS = [
    "Documentation chunk preview only. Chunks are deterministic excerpts from allowlisted Dav AI documentation.",
    "No embeddings, vector database, RAG, LLM, generated answers, or safety decisions are used.",
    "Not medical advice.",
    "Not a safety determination for any product, drug, food, supplement, or cosmetic.",
    "Verify official FDA/USDA sources before acting.",
]

DEFAULT_MAX_CHUNK_CHARACTERS = 1600
MAX_CHUNK_PREVIEW_RESULTS = 100

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class MarkdownSection:
    start_index: int
    end_index: int
    heading: str | None


@dataclass(frozen=True)
class TextSpan:
    text: str
    line_start: int
    line_end: int


def _extract_title(lines: list[str], fallback: str) -> str:
    for line in lines:
        match = HEADING_PATTERN.match(line)
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()

    return fallback


def _markdown_sections(lines: list[str]) -> list[MarkdownSection]:
    if not lines:
        return []

    heading_indexes: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match:
            heading_indexes.append((index, match.group(2).strip()))

    if not heading_indexes:
        return [
            MarkdownSection(
                start_index=0,
                end_index=len(lines),
                heading=None,
            )
        ]

    sections: list[MarkdownSection] = []
    first_heading_index = heading_indexes[0][0]
    if first_heading_index > 0:
        sections.append(
            MarkdownSection(
                start_index=0,
                end_index=first_heading_index,
                heading=None,
            )
        )

    for position, (start_index, heading) in enumerate(heading_indexes):
        next_position = position + 1
        end_index = (
            heading_indexes[next_position][0]
            if next_position < len(heading_indexes)
            else len(lines)
        )
        sections.append(
            MarkdownSection(
                start_index=start_index,
                end_index=end_index,
                heading=heading,
            )
        )

    return sections


def _paragraph_spans(
    lines: list[str],
    start_index: int,
    end_index: int,
) -> list[TextSpan]:
    spans: list[TextSpan] = []
    paragraph_start: int | None = None
    paragraph_lines: list[str] = []

    def flush_paragraph(end_line_index: int) -> None:
        nonlocal paragraph_start, paragraph_lines
        if paragraph_start is None or not paragraph_lines:
            return

        text = "\n".join(line.rstrip() for line in paragraph_lines).strip()
        if text:
            spans.append(
                TextSpan(
                    text=text,
                    line_start=paragraph_start + 1,
                    line_end=end_line_index,
                )
            )

        paragraph_start = None
        paragraph_lines = []

    for index in range(start_index, end_index):
        line = lines[index]
        if line.strip():
            if paragraph_start is None:
                paragraph_start = index
            paragraph_lines.append(line)
        else:
            flush_paragraph(index)

    flush_paragraph(end_index)
    return spans


def _split_long_span(span: TextSpan, max_characters: int) -> list[TextSpan]:
    text = span.text
    chunks: list[TextSpan] = []

    while len(text) > max_characters:
        split_at = text.rfind(" ", 0, max_characters + 1)
        if split_at < max_characters // 2:
            split_at = max_characters

        chunk_text = text[:split_at].strip()
        if chunk_text:
            chunks.append(
                TextSpan(
                    text=chunk_text,
                    line_start=span.line_start,
                    line_end=span.line_end,
                )
            )

        text = text[split_at:].strip()

    if text:
        chunks.append(
            TextSpan(
                text=text,
                line_start=span.line_start,
                line_end=span.line_end,
            )
        )

    return chunks


def _chunk_section_text(
    lines: list[str],
    section: MarkdownSection,
    max_characters: int,
) -> list[TextSpan]:
    paragraphs = _paragraph_spans(lines, section.start_index, section.end_index)
    chunks: list[TextSpan] = []
    current_parts: list[str] = []
    current_start = 0
    current_end = 0

    def flush_current() -> None:
        nonlocal current_parts, current_start, current_end
        if not current_parts:
            return

        chunks.append(
            TextSpan(
                text="\n\n".join(current_parts),
                line_start=current_start,
                line_end=current_end,
            )
        )
        current_parts = []
        current_start = 0
        current_end = 0

    for paragraph in paragraphs:
        if len(paragraph.text) > max_characters:
            flush_current()
            chunks.extend(_split_long_span(paragraph, max_characters))
            continue

        next_text = (
            paragraph.text
            if not current_parts
            else "\n\n".join([*current_parts, paragraph.text])
        )
        if len(next_text) > max_characters:
            flush_current()

        if not current_parts:
            current_start = paragraph.line_start
        current_parts.append(paragraph.text)
        current_end = paragraph.line_end

    flush_current()
    return chunks


def _content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _chunk_id(source_path: str, line_start: int, line_end: int, content_hash: str) -> str:
    raw_id = f"{source_path}:{line_start}:{line_end}:{content_hash}"
    return f"docs-{sha256(raw_id.encode('utf-8')).hexdigest()[:24]}"


def build_static_docs_chunks(
    repo_root: Path | None = None,
    max_chunk_characters: int = DEFAULT_MAX_CHUNK_CHARACTERS,
) -> list[StaticDocsChunkPreview]:
    chunks: list[StaticDocsChunkPreview] = []
    effective_max_characters = max(1, max_chunk_characters)

    for doc in get_searchable_docs(repo_root):
        text = doc.path.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = _extract_title(lines, fallback=doc.path.stem.replace("_", " ").title())

        for section in _markdown_sections(lines):
            for span in _chunk_section_text(lines, section, effective_max_characters):
                digest = _content_hash(span.text)
                chunks.append(
                    StaticDocsChunkPreview(
                        chunk_id=_chunk_id(
                            doc.source_path,
                            span.line_start,
                            span.line_end,
                            digest,
                        ),
                        source_path=doc.source_path,
                        title=title,
                        section_heading=section.heading,
                        text=span.text,
                        line_start=span.line_start,
                        line_end=span.line_end,
                        character_count=len(span.text),
                        content_hash=digest,
                    )
                )

    return chunks


def preview_static_docs_chunks(
    max_results: int = 20,
    repo_root: Path | None = None,
) -> list[StaticDocsChunkPreview]:
    bounded_limit = max(1, min(max_results, MAX_CHUNK_PREVIEW_RESULTS))
    return build_static_docs_chunks(repo_root=repo_root)[:bounded_limit]
