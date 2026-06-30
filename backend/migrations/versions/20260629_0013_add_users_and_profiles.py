"""Add portfolio-demo users and profiles.

Revision ID: 20260629_0013
Revises: 20260626_0012
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260629_0013"
down_revision = "20260626_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
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
        sa.CheckConstraint(
            "length(trim(full_name)) >= 2",
            name="users_full_name_length_check",
        ),
        sa.CheckConstraint(
            "position('@' in email) > 1",
            name="users_email_format_check",
        ),
        sa.CheckConstraint(
            "length(trim(password_hash)) > 0",
            name="users_password_hash_present_check",
        ),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_created_at", "users", ["created_at"])

    op.create_table(
        "user_profiles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("zip_code", sa.Text(), nullable=True),
        sa.Column(
            "alert_interests",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("alert_frequency", sa.Text(), nullable=True),
        sa.Column("report_style", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            """
            role is null or role in (
                'consumer',
                'pharmacy',
                'clinic',
                'public_health_analyst',
                'student_researcher'
            )
            """,
            name="user_profiles_role_check",
        ),
        sa.CheckConstraint(
            "alert_frequency is null or alert_frequency in ('none', 'weekly', 'monthly')",
            name="user_profiles_alert_frequency_check",
        ),
        sa.CheckConstraint(
            """
            report_style is null or report_style in (
                'simple',
                'technical',
                'pharmacy_clinic'
            )
            """,
            name="user_profiles_report_style_check",
        ),
    )
    op.create_index("idx_user_profiles_role", "user_profiles", ["role"])
    op.create_index("idx_user_profiles_state", "user_profiles", ["state"])


def downgrade() -> None:
    op.drop_index("idx_user_profiles_state", table_name="user_profiles")
    op.drop_index("idx_user_profiles_role", table_name="user_profiles")
    op.drop_table("user_profiles")
    op.drop_index("idx_users_created_at", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
