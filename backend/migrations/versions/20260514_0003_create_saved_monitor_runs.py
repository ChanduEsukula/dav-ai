"""create saved_monitor_runs table

Revision ID: 20260514_0003
Revises: 20260511_0002
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260514_0003"
down_revision = "20260511_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_monitor_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "monitor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("saved_monitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("module", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("score_label", sa.Text(), nullable=True),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "module in ('recallradar', 'drugsignal')",
            name="saved_monitor_runs_module_check",
        ),
        sa.CheckConstraint(
            "status in ('success', 'error')",
            name="saved_monitor_runs_status_check",
        ),
        sa.CheckConstraint(
            "record_count is null or record_count >= 0",
            name="saved_monitor_runs_record_count_check",
        ),
        sa.CheckConstraint(
            "score is null or score >= 0",
            name="saved_monitor_runs_score_check",
        ),
    )

    op.create_index(
        "idx_saved_monitor_runs_monitor_id_created_at",
        "saved_monitor_runs",
        ["monitor_id", "created_at"],
    )
    op.create_index("idx_saved_monitor_runs_status", "saved_monitor_runs", ["status"])


def downgrade() -> None:
    op.drop_index("idx_saved_monitor_runs_status", table_name="saved_monitor_runs")
    op.drop_index(
        "idx_saved_monitor_runs_monitor_id_created_at",
        table_name="saved_monitor_runs",
    )
    op.drop_table("saved_monitor_runs")
