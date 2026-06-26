"""Add RealWorldSafety to audit event module constraint.

Revision ID: 20260626_0012
Revises: 20260622_0011
Create Date: 2026-06-26
"""

from alembic import op

revision = "20260626_0012"
down_revision = "20260622_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        alter table audit_events
        drop constraint if exists audit_events_module_check
        """
    )
    op.execute(
        """
        alter table audit_events
        add constraint audit_events_module_check
        check (
            module in (
                'RecallRadar',
                'DrugSignal',
                'CosmeticSignal',
                'FoodRadar',
                'RegionalHealthPulse',
                'RealWorldSafety'
            )
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        alter table audit_events
        drop constraint if exists audit_events_module_check
        """
    )
    op.execute(
        """
        alter table audit_events
        add constraint audit_events_module_check
        check (
            module in (
                'RecallRadar',
                'DrugSignal',
                'CosmeticSignal',
                'FoodRadar',
                'RegionalHealthPulse'
            )
        )
        """
    )
