"""Register the pharmaceutical communications source, separate from device notices."""
from alembic import op

revision = "20260925_0017"
down_revision = "20260925_0016"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""INSERT INTO source_registry (source_id, source_name, endpoint, module, description, update_cadence)
    VALUES (
            'fda_drug_safety_communications',
            'FDA Drug Safety Communications',
            'https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications',
            'RealWorldSafety',
            'Maintained collection of official pharmaceutical safety communications ingested into the stored drug catalog.',
            'Periodic refresh of configured official URLs'
    ) ON CONFLICT (source_id) DO NOTHING""")


def downgrade():
    op.execute("DELETE FROM source_registry WHERE source_id='fda_drug_safety_communications'")
