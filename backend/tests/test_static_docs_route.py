from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.static_docs_retrieval import get_searchable_docs, search_static_docs


client = TestClient(app)


def test_docs_search_finds_productscan_docs():
    response = client.get(
        "/api/v1/docs/search",
        params={"q": "ProductScan browser OCR", "max_results": 10},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "ProductScan browser OCR"
    assert body["count"] > 0
    assert any(
        result["source_path"] == "docs/productscan/PRODUCTSCAN_OCR_V2_PLAN.md"
        for result in body["results"]
    )

    first_result = body["results"][0]
    assert first_result["title"]
    assert first_result["source_path"].endswith(".md")
    assert first_result["snippet"]
    assert first_result["matched_terms"]
    assert first_result["line_start"] >= 1
    assert first_result["line_end"] >= first_result["line_start"]


def test_docs_search_finds_vector_db_rag_plan_docs():
    response = client.get(
        "/api/v1/docs/search",
        params={"q": "pgvector RAG citations unavailable", "max_results": 8},
    )

    assert response.status_code == 200
    body = response.json()

    vector_results = [
        result
        for result in body["results"]
        if result["source_path"] == "docs/architecture/VECTOR_DB_RAG_PLAN.md"
    ]
    assert vector_results
    assert any("RAG" in result["title"] for result in vector_results)
    assert any(result["section_heading"] for result in vector_results)


def test_docs_search_returns_empty_results_with_limitations_for_unknown_query():
    response = client.get(
        "/api/v1/docs/search",
        params={"q": "zzzznonexistentdocsphrase"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 0
    assert body["results"] == []
    assert "Documentation search only" in body["limitations"][0]
    assert "Not medical advice." in body["limitations"]
    assert "Not a safety determination" in " ".join(body["limitations"])
    assert "Verify official FDA/USDA sources before acting." in body["limitations"]


def test_docs_search_validates_query_and_max_results():
    short_response = client.get("/api/v1/docs/search", params={"q": "x"})
    assert short_response.status_code == 422

    blank_response = client.get("/api/v1/docs/search", params={"q": "   "})
    assert blank_response.status_code == 400
    assert blank_response.json()["detail"]["code"] == "DOCS_QUERY_TOO_SHORT"

    long_query_response = client.get(
        "/api/v1/docs/search",
        params={"q": "a" * 121},
    )
    assert long_query_response.status_code == 422

    max_results_response = client.get(
        "/api/v1/docs/search",
        params={"q": "ProductScan", "max_results": 21},
    )
    assert max_results_response.status_code == 422


def test_docs_search_limits_result_count():
    response = client.get(
        "/api/v1/docs/search",
        params={"q": "safety source public", "max_results": 3},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] <= 3
    assert len(body["results"]) <= 3


def test_static_docs_allowlist_excludes_private_files(tmp_path: Path):
    (tmp_path / "README.md").write_text("Public readme content\n", encoding="utf-8")
    architecture_dir = tmp_path / "docs" / "architecture"
    architecture_dir.mkdir(parents=True)
    (architecture_dir / "allowed.md").write_text(
        "# Allowed Doc\nsafeallowlistterm appears here\n",
        encoding="utf-8",
    )
    private_dir = tmp_path / "backend"
    private_dir.mkdir()
    (private_dir / "private.md").write_text(
        "# Private Doc\nprivatedocterm should not be indexed\n",
        encoding="utf-8",
    )
    nested_dir = architecture_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "nested.md").write_text(
        "# Nested Doc\nnesteddocsecret should not be indexed\n",
        encoding="utf-8",
    )

    indexed_paths = {doc.source_path for doc in get_searchable_docs(tmp_path)}

    assert indexed_paths == {"README.md", "docs/architecture/allowed.md"}
    assert search_static_docs("safeallowlistterm", repo_root=tmp_path)
    assert search_static_docs("privatedocterm", repo_root=tmp_path) == []
    assert search_static_docs("nesteddocsecret", repo_root=tmp_path) == []
