"""add saved monitor schedule fields

Revision ID: 20260514_0004
Revises: 20260514_0003
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260514_0004"
down_revision = "20260514_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_monitors",
        sa.Column(
            "refresh_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "saved_monitors",
        sa.Column("refresh_interval_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "saved_monitors",
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saved_monitors",
        sa.Column("last_scheduled_run_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saved_monitors",
        sa.Column("last_scheduled_status", sa.Text(), nullable=True),
    )

    op.create_index(
        "idx_saved_monitors_due_refresh",
        "saved_monitors",
        ["refresh_enabled", "next_run_at"],
    )

    op.create_check_constraint(
        "saved_monitors_refresh_interval_check",
        "saved_monitors",
        "refresh_interval_minutes IS NULL OR refresh_interval_minutes > 0",
    )
    op.create_check_constraint(
        "saved_monitors_last_scheduled_status_check",
        "saved_monitors",
        "last_scheduled_status IS NULL OR last_scheduled_status IN ('success', 'error', 'skipped')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "saved_monitors_last_scheduled_status_check",
        "saved_monitors",
        type_="check",
    )
    op.drop_constraint(
        "saved_monitors_refresh_interval_check",
        "saved_monitors",
        type_="check",
    )
    op.drop_index("idx_saved_monitors_due_refresh", table_name="saved_monitors")
    op.drop_column("saved_monitors", "last_scheduled_status")
    op.drop_column("saved_monitors", "last_scheduled_run_at")
    op.drop_column("saved_monitors", "next_run_at")
    op.drop_column("saved_monitors", "refresh_interval_minutes")
    op.drop_column("saved_monitors", "refresh_enabled")