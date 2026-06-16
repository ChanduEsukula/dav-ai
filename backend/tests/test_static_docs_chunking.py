from pathlib import Path
import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.static_docs_chunking import build_static_docs_chunks


client = TestClient(app)


def write_allowed_doc(repo_root: Path, relative_path: str, text: str) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_chunks_are_generated_from_allowlisted_docs(tmp_path: Path):
    write_allowed_doc(
        tmp_path,
        "README.md",
        "# Dav AI\n\nDocumentation search only foundation.\n",
    )
    write_allowed_doc(
        tmp_path,
        "docs/architecture/vector.md",
        "# Vector Plan\n\n## Purpose\n\nDeterministic docs chunks.\n",
    )

    chunks = build_static_docs_chunks(repo_root=tmp_path)
    source_paths = {chunk.source_path for chunk in chunks}

    assert "README.md" in source_paths
    assert "docs/architecture/vector.md" in source_paths
    assert chunks


def test_chunks_include_stable_ids_line_ranges_and_content_hash(tmp_path: Path):
    write_allowed_doc(
        tmp_path,
        "docs/productscan/PRODUCTSCAN.md",
        "# ProductScan\n\n## Browser OCR\n\nUser reviewed label text only.\n",
    )

    first_run = build_static_docs_chunks(repo_root=tmp_path)
    second_run = build_static_docs_chunks(repo_root=tmp_path)

    assert [chunk.chunk_id for chunk in first_run] == [
        chunk.chunk_id for chunk in second_run
    ]

    chunk = first_run[0]
    assert chunk.chunk_id.startswith("docs-")
    assert re.fullmatch(r"[a-f0-9]{64}", chunk.content_hash)
    assert chunk.source_path == "docs/productscan/PRODUCTSCAN.md"
    assert chunk.line_start >= 1
    assert chunk.line_end >= chunk.line_start


def test_chunks_preserve_markdown_section_headings(tmp_path: Path):
    write_allowed_doc(
        tmp_path,
        "docs/demo/PORTFOLIO_DEMO_PACKAGE.md",
        "# Demo Package\n\n## Source Guidance\n\nVerify official sources.\n",
    )

    chunks = build_static_docs_chunks(repo_root=tmp_path)

    assert any(
        chunk.section_heading == "Source Guidance"
        and "Verify official sources." in chunk.text
        for chunk in chunks
    )


def test_chunk_size_limit_is_respected(tmp_path: Path):
    long_text = " ".join(["documentation"] * 60)
    write_allowed_doc(
        tmp_path,
        "docs/architecture/large.md",
        f"# Large Doc\n\n## Oversized Section\n\n{long_text}\n",
    )

    chunks = build_static_docs_chunks(
        repo_root=tmp_path,
        max_chunk_characters=80,
    )

    assert len(chunks) > 1
    assert all(chunk.character_count <= 80 for chunk in chunks)


def test_disallowed_docs_are_not_included_in_chunks(tmp_path: Path):
    write_allowed_doc(
        tmp_path,
        "docs/architecture/allowed.md",
        "# Allowed\n\nsafechunkterm appears here.\n",
    )
    write_allowed_doc(
        tmp_path,
        "backend/private.md",
        "# Private\n\nprivatechunkterm should not appear.\n",
    )
    write_allowed_doc(
        tmp_path,
        "docs/architecture/nested/private.md",
        "# Nested\n\nnestedchunkterm should not appear.\n",
    )

    chunks = build_static_docs_chunks(repo_root=tmp_path)
    combined_text = "\n".join(chunk.text for chunk in chunks)
    source_paths = {chunk.source_path for chunk in chunks}

    assert source_paths == {"docs/architecture/allowed.md"}
    assert "safechunkterm" in combined_text
    assert "privatechunkterm" not in combined_text
    assert "nestedchunkterm" not in combined_text


def test_docs_chunks_preview_route_validates_limit_and_returns_limitations():
    response = client.get("/api/v1/docs/chunks", params={"max_results": 2})

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 2
    assert len(body["chunks"]) == 2
    assert "Documentation chunk preview only" in body["limitations"][0]
    assert "No embeddings" in " ".join(body["limitations"])
    assert "Not medical advice." in body["limitations"]

    too_small_response = client.get("/api/v1/docs/chunks", params={"max_results": 0})
    assert too_small_response.status_code == 422

    too_large_response = client.get("/api/v1/docs/chunks", params={"max_results": 101})
    assert too_large_response.status_code == 422
