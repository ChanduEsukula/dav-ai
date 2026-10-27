"""Durable label bulk progress; commit checkpoints with record batches."""
from alembic import op
revision = '20260926_0018'
down_revision = '20260925_0017'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE pharma.drug_labels ALTER COLUMN title DROP NOT NULL")
    op.execute('''CREATE TABLE pharma.bulk_label_files (
        dataset_key text NOT NULL, file_url text NOT NULL,
        source_export_date text NOT NULL, expected_records integer NOT NULL,
        processed integer NOT NULL DEFAULT 0,
        counts jsonb NOT NULL DEFAULT '{}',
        sha256 text, status text NOT NULL DEFAULT 'pending', error text,
        ingestion_run_id uuid NOT NULL REFERENCES pharma.ingestion_runs(id),
        updated_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY(dataset_key, file_url),
        CHECK(status IN ('pending','running','succeeded','partial','failed')),
        CHECK(processed >= 0 AND expected_records >= 0)
    )''')


def downgrade():
    op.execute('DROP TABLE pharma.bulk_label_files')
    # Preserve legitimate NULL titles; never invent values to satisfy an older constraint.
