"""Create scheduler locks table.

Revision ID: 20260519_0005
Revises: 20260514_0004
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260519_0005"
down_revision: Union[str, None] = "20260514_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduler_locks",
        sa.Column("lock_name", sa.Text(), primary_key=True),
        sa.Column("locked_by", sa.Text(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "idx_scheduler_locks_locked_until",
        "scheduler_locks",
        ["locked_until"],
    )


def downgrade() -> None:
    op.drop_index("idx_scheduler_locks_locked_until", table_name="scheduler_locks")
    op.drop_table("scheduler_locks")
