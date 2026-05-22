"""Create source pulls and raw source snapshots.

Revision ID: 20260521_0006
Revises: 20260519_0005
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260521_0006"
down_revision: Union[str, None] = "20260519_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_pulls",
        sa.Column("pull_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_events.audit_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "source_id",
            sa.Text(),
            sa.ForeignKey("source_registry.source_id"),
            nullable=False,
        ),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column(
            "query_params",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("upstream_status", sa.Text(), nullable=False),
        sa.Column(
            "record_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("payload_hash", sa.Text(), nullable=False),
        sa.Column("transform_version", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "upstream_status in ('success', 'empty', 'error')",
            name="source_pulls_upstream_status_check",
        ),
        sa.CheckConstraint(
            "record_count >= 0",
            name="source_pulls_record_count_check",
        ),
    )

    op.create_table(
        "raw_source_snapshots",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "pull_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_pulls.pull_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "idx_source_pulls_audit_id",
        "source_pulls",
        ["audit_id"],
    )
    op.create_index(
        "idx_source_pulls_source_id_created_at",
        "source_pulls",
        ["source_id", sa.text("created_at desc")],
    )
    op.create_index(
        "idx_source_pulls_upstream_status",
        "source_pulls",
        ["upstream_status"],
    )
    op.create_index(
        "idx_source_pulls_payload_hash",
        "source_pulls",
        ["payload_hash"],
    )
    op.create_index(
        "idx_raw_source_snapshots_pull_id",
        "raw_source_snapshots",
        ["pull_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_raw_source_snapshots_pull_id", table_name="raw_source_snapshots")
    op.drop_index("idx_source_pulls_payload_hash", table_name="source_pulls")
    op.drop_index("idx_source_pulls_upstream_status", table_name="source_pulls")
    op.drop_index("idx_source_pulls_source_id_created_at", table_name="source_pulls")
    op.drop_index("idx_source_pulls_audit_id", table_name="source_pulls")

    op.drop_table("raw_source_snapshots")
    op.drop_table("source_pulls")
