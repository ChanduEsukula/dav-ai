"""Add user ownership to saved monitors.

Revision ID: 20260629_0014
Revises: 20260629_0013
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260629_0014"
down_revision = "20260629_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_monitors",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_saved_monitors_user_id_users",
        "saved_monitors",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_saved_monitors_user_id",
        "saved_monitors",
        ["user_id"],
    )
    op.execute(
        """
        create unique index if not exists
            idx_saved_monitors_user_module_normalized_query
        on saved_monitors (
            user_id,
            module,
            lower(trim(query))
        )
        where user_id is not null
        """
    )


def downgrade() -> None:
    op.execute(
        """
        drop index if exists idx_saved_monitors_user_module_normalized_query
        """
    )
    op.drop_index("idx_saved_monitors_user_id", table_name="saved_monitors")
    op.drop_constraint(
        "fk_saved_monitors_user_id_users",
        "saved_monitors",
        type_="foreignkey",
    )
    op.drop_column("saved_monitors", "user_id")
