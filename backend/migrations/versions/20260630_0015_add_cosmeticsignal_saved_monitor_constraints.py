"""Add CosmeticSignal to saved monitor constraints.

Revision ID: 20260630_0015
Revises: 20260629_0014
Create Date: 2026-06-30
"""

from alembic import op


revision = "20260630_0015"
down_revision = "20260629_0014"
branch_labels = None
depends_on = None


UPGRADED_MODULE_CHECK = (
    "check (module in ("
    "'recallradar', "
    "'drugsignal', "
    "'foodradar', "
    "'cosmeticsignal', "
    "'regional_health_pulse'"
    "))"
)

DOWNGRADED_MODULE_CHECK = (
    "check (module in ("
    "'recallradar', "
    "'drugsignal', "
    "'foodradar', "
    "'regional_health_pulse'"
    "))"
)


def upgrade() -> None:
    op.execute(
        """
        alter table saved_monitors
        drop constraint if exists saved_monitors_module_check
        """
    )
    op.execute(
        f"""
        alter table saved_monitors
        add constraint saved_monitors_module_check
        {UPGRADED_MODULE_CHECK}
        """
    )

    op.execute(
        """
        alter table saved_monitor_runs
        drop constraint if exists saved_monitor_runs_module_check
        """
    )
    op.execute(
        f"""
        alter table saved_monitor_runs
        add constraint saved_monitor_runs_module_check
        {UPGRADED_MODULE_CHECK}
        """
    )


def downgrade() -> None:
    op.execute(
        """
        alter table saved_monitor_runs
        drop constraint if exists saved_monitor_runs_module_check
        """
    )
    op.execute(
        f"""
        alter table saved_monitor_runs
        add constraint saved_monitor_runs_module_check
        {DOWNGRADED_MODULE_CHECK}
        """
    )

    op.execute(
        """
        alter table saved_monitors
        drop constraint if exists saved_monitors_module_check
        """
    )
    op.execute(
        f"""
        alter table saved_monitors
        add constraint saved_monitors_module_check
        {DOWNGRADED_MODULE_CHECK}
        """
    )
