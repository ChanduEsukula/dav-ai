"""Align Regional Health Pulse source and saved monitor constraints.

Revision ID: 20260527_0007
Revises: 20260521_0006
Create Date: 2026-05-27
"""

from alembic import op


revision = "20260527_0007"
down_revision = "20260521_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        insert into source_registry (
            source_id,
            source_name,
            endpoint,
            module,
            description,
            update_cadence
        )
        values (
            'regional_health_pulse_demo',
            'Regional Health Pulse MVP scaffold',
            'https://healthdata.gov/',
            'RegionalHealthPulse',
            'Demo public-health signal scaffold for Regional Health Pulse backend v1. This is not live CDC/HHS surveillance yet.',
            'MVP scaffold; live public source cadence not configured yet'
        )
        on conflict (source_id) do update set
            source_name = excluded.source_name,
            endpoint = excluded.endpoint,
            module = excluded.module,
            description = excluded.description,
            update_cadence = excluded.update_cadence,
            updated_at = now()
        """
    )

    op.execute(
        """
        alter table saved_monitors
        drop constraint if exists saved_monitors_module_check
        """
    )
    op.execute(
        """
        alter table saved_monitors
        add constraint saved_monitors_module_check
        check (module in ('recallradar', 'drugsignal', 'regional_health_pulse'))
        """
    )

    op.execute(
        """
        alter table saved_monitor_runs
        drop constraint if exists saved_monitor_runs_module_check
        """
    )
    op.execute(
        """
        alter table saved_monitor_runs
        add constraint saved_monitor_runs_module_check
        check (module in ('recallradar', 'drugsignal', 'regional_health_pulse'))
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
        """
        alter table saved_monitor_runs
        add constraint saved_monitor_runs_module_check
        check (module in ('recallradar', 'drugsignal'))
        """
    )

    op.execute(
        """
        alter table saved_monitors
        drop constraint if exists saved_monitors_module_check
        """
    )
    op.execute(
        """
        alter table saved_monitors
        add constraint saved_monitors_module_check
        check (module in ('recallradar', 'drugsignal'))
        """
    )

    op.execute(
        """
        delete from source_registry
        where source_id = 'regional_health_pulse_demo'
        """
    )