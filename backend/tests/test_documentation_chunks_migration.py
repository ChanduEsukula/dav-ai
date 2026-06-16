from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    REPO_ROOT
    / "backend"
    / "migrations"
    / "versions"
    / "20260616_0010_create_documentation_chunks.py"
)


def test_documentation_chunks_migration_defines_expected_table_and_revision():
    migration_source = MIGRATION_PATH.read_text()

    assert 'revision = "20260616_0010"' in migration_source
    assert 'down_revision = "20260608_0009"' in migration_source
    assert '"documentation_chunks"' in migration_source
    assert "op.create_table(" in migration_source


def test_documentation_chunks_migration_includes_expected_columns():
    migration_source = MIGRATION_PATH.read_text()

    for column in [
        "id",
        "chunk_id",
        "source_path",
        "title",
        "section_heading",
        "line_start",
        "line_end",
        "text",
        "character_count",
        "content_hash",
        "embedding_provider",
        "embedding_model",
        "embedding_dimension",
        "embedding_preview",
        "embedding_status",
        "created_at",
        "updated_at",
    ]:
        assert f'"{column}"' in migration_source

    assert "postgresql.JSONB" in migration_source


def test_documentation_chunks_migration_includes_constraints_and_indexes():
    migration_source = MIGRATION_PATH.read_text()

    for expected in [
        "uq_documentation_chunks_chunk_id",
        "documentation_chunks_line_start_check",
        "line_start > 0",
        "documentation_chunks_line_range_check",
        "line_end >= line_start",
        "documentation_chunks_character_count_check",
        "character_count > 0",
        "documentation_chunks_embedding_dimension_check",
        "embedding_dimension is null or embedding_dimension > 0",
        "documentation_chunks_embedding_status_check",
        "embedding_status in ('not_embedded', 'preview', 'embedded', 'error')",
        "idx_documentation_chunks_source_path",
        "idx_documentation_chunks_content_hash",
        "idx_documentation_chunks_embedding_status",
        "idx_documentation_chunks_source_path_content_hash",
    ]:
        assert expected in migration_source


def test_documentation_chunks_migration_defers_pgvector_and_extension_work():
    migration_source = MIGRATION_PATH.read_text().lower()

    assert "create extension" not in migration_source
    assert "pgvector" not in migration_source
    assert "vector(" not in migration_source
    assert 'sa.column("embedding"' not in migration_source
    assert '"embedding_preview"' in migration_source
