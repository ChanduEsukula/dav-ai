"""create source registry and audit events

Revision ID: 20260505_0001
Revises:
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260505_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_registry",
        sa.Column("source_id", sa.Text(), primary_key=True),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("module", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("update_cadence", sa.Text(), nullable=False),
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
    )

    op.create_table(
        "audit_events",
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module", sa.Text(), nullable=False),
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
        sa.Column("transform_version", sa.Text(), nullable=False),
        sa.Column("score_version", sa.Text(), nullable=True),
        sa.Column("disclaimer_version", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "upstream_status in ('success', 'empty', 'error')",
            name="audit_events_upstream_status_check",
        ),
        sa.CheckConstraint(
            "record_count >= 0",
            name="audit_events_record_count_check",
        ),
    )

    op.create_index(
        "idx_audit_events_source_id",
        "audit_events",
        ["source_id"],
    )
    op.create_index(
        "idx_audit_events_module",
        "audit_events",
        ["module"],
    )
    op.create_index(
        "idx_audit_events_created_at",
        "audit_events",
        [sa.text("created_at desc")],
    )
    op.create_index(
        "idx_audit_events_upstream_status",
        "audit_events",
        ["upstream_status"],
    )

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
        values
            (
                'openfda_drug_enforcement',
                'openFDA Drug Enforcement API',
                'https://api.fda.gov/drug/enforcement.json',
                'RecallRadar',
                'Drug recall enforcement records from openFDA.',
                'Source-dependent FDA updates'
            ),
            (
                'openfda_drug_event',
                'openFDA Drug Event API',
                'https://api.fda.gov/drug/event.json',
                'DrugSignal',
                'FAERS adverse-event and medication-error reports from openFDA.',
                'Periodic FDA FAERS updates'
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


def downgrade() -> None:
    op.drop_index("idx_audit_events_upstream_status", table_name="audit_events")
    op.drop_index("idx_audit_events_created_at", table_name="audit_events")
    op.drop_index("idx_audit_events_module", table_name="audit_events")
    op.drop_index("idx_audit_events_source_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("source_registry")
