"""Create documentation chunks table.

Revision ID: 20260616_0010
Revises: 20260608_0009
Create Date: 2026-06-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260616_0010"
down_revision = "20260608_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documentation_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chunk_id", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("section_heading", sa.Text(), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=False),
        sa.Column("line_end", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("embedding_provider", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.Text(), nullable=True),
        sa.Column("embedding_dimension", sa.Integer(), nullable=True),
        sa.Column("embedding_preview", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "embedding_status",
            sa.Text(),
            server_default=sa.text("'not_embedded'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "chunk_id",
            name="uq_documentation_chunks_chunk_id",
        ),
        sa.CheckConstraint(
            "line_start > 0",
            name="documentation_chunks_line_start_check",
        ),
        sa.CheckConstraint(
            "line_end >= line_start",
            name="documentation_chunks_line_range_check",
        ),
        sa.CheckConstraint(
            "character_count > 0",
            name="documentation_chunks_character_count_check",
        ),
        sa.CheckConstraint(
            "embedding_dimension is null or embedding_dimension > 0",
            name="documentation_chunks_embedding_dimension_check",
        ),
        sa.CheckConstraint(
            "embedding_status in ('not_embedded', 'preview', 'embedded', 'error')",
            name="documentation_chunks_embedding_status_check",
        ),
    )

    op.create_index(
        "idx_documentation_chunks_source_path",
        "documentation_chunks",
        ["source_path"],
    )
    op.create_index(
        "idx_documentation_chunks_content_hash",
        "documentation_chunks",
        ["content_hash"],
    )
    op.create_index(
        "idx_documentation_chunks_embedding_status",
        "documentation_chunks",
        ["embedding_status"],
    )
    op.create_index(
        "idx_documentation_chunks_source_path_content_hash",
        "documentation_chunks",
        ["source_path", "content_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_documentation_chunks_source_path_content_hash",
        table_name="documentation_chunks",
    )
    op.drop_index(
        "idx_documentation_chunks_embedding_status",
        table_name="documentation_chunks",
    )
    op.drop_index(
        "idx_documentation_chunks_content_hash",
        table_name="documentation_chunks",
    )
    op.drop_index(
        "idx_documentation_chunks_source_path",
        table_name="documentation_chunks",
    )
    op.drop_table("documentation_chunks")
