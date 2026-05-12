"""create saved_monitors table

Revision ID: 20260511_0002
Revises: 20260505_0001
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260511_0002"
down_revision = "20260505_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_monitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("module", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latest_audit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latest_score", sa.Integer(), nullable=True),
        sa.Column("previous_score", sa.Integer(), nullable=True),
        sa.Column("latest_record_count", sa.Integer(), nullable=True),
        sa.Column("previous_record_count", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'not_checked'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "module in ('recallradar', 'drugsignal')",
            name="saved_monitors_module_check",
        ),
        sa.CheckConstraint(
            "status in ('not_checked', 'checked', 'error')",
            name="saved_monitors_status_check",
        ),
        sa.CheckConstraint(
            "latest_score is null or latest_score >= 0",
            name="saved_monitors_latest_score_check",
        ),
        sa.CheckConstraint(
            "previous_score is null or previous_score >= 0",
            name="saved_monitors_previous_score_check",
        ),
        sa.CheckConstraint(
            "latest_record_count is null or latest_record_count >= 0",
            name="saved_monitors_latest_record_count_check",
        ),
        sa.CheckConstraint(
            "previous_record_count is null or previous_record_count >= 0",
            name="saved_monitors_previous_record_count_check",
        ),
    )

    op.create_index("idx_saved_monitors_module", "saved_monitors", ["module"])
    op.create_index("idx_saved_monitors_status", "saved_monitors", ["status"])
    op.create_index("idx_saved_monitors_created_at", "saved_monitors", ["created_at"])
    op.create_index(
        "idx_saved_monitors_last_checked_at",
        "saved_monitors",
        ["last_checked_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_saved_monitors_last_checked_at", table_name="saved_monitors")
    op.drop_index("idx_saved_monitors_created_at", table_name="saved_monitors")
    op.drop_index("idx_saved_monitors_status", table_name="saved_monitors")
    op.drop_index("idx_saved_monitors_module", table_name="saved_monitors")
    op.drop_table("saved_monitors")
