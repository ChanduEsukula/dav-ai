"""Add the pharmaceutical MVP without changing existing application tables."""
from alembic import op

revision = "20260925_0016"
down_revision = "20260630_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA pharma")
    op.execute("""
        CREATE TABLE pharma.ingestion_runs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            source text NOT NULL REFERENCES source_registry(source_id),
            status text NOT NULL DEFAULT 'running'
                CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
            started_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz,
            parameters jsonb NOT NULL DEFAULT '{}',
            records_fetched integer NOT NULL DEFAULT 0 CHECK (records_fetched >= 0),
            records_inserted integer NOT NULL DEFAULT 0 CHECK (records_inserted >= 0),
            records_updated integer NOT NULL DEFAULT 0 CHECK (records_updated >= 0),
            records_unresolved integer NOT NULL DEFAULT 0 CHECK (records_unresolved >= 0),
            records_failed integer NOT NULL DEFAULT 0 CHECK (records_failed >= 0),
            coverage jsonb NOT NULL DEFAULT '{}',
            error_summary text,
            CHECK (finished_at IS NULL OR finished_at >= started_at),
            UNIQUE (id, source)
        )
    """)
    provenance = """
        source text NOT NULL REFERENCES source_registry(source_id),
        source_record_id text NOT NULL CHECK (length(trim(source_record_id)) > 0),
        source_url text,
        source_updated_at timestamptz,
        ingested_at timestamptz NOT NULL DEFAULT now(),
        ingestion_run_id uuid NOT NULL,
        raw_json jsonb NOT NULL DEFAULT '{}',
        FOREIGN KEY (ingestion_run_id, source) REFERENCES pharma.ingestion_runs(id, source),
        UNIQUE (source, source_record_id)
    """
    columns = {
        "drugs": """
            generic_name text NOT NULL CHECK (length(trim(generic_name)) > 0),
            normalized_generic_name text NOT NULL,
            brand_names text[] NOT NULL DEFAULT '{}',
            normalized_names text[] NOT NULL DEFAULT '{}',
            active_ingredients text[] NOT NULL DEFAULT '{}',
            strength text, dosage_form text,
            routes text[] NOT NULL DEFAULT '{}',
            manufacturers text[] NOT NULL DEFAULT '{}',
            rxcui text,
            product_ndcs text[] NOT NULL DEFAULT '{}',
            package_ndcs text[] NOT NULL DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now(),
        """,
        "drug_labels": """
            label_set_id text, label_version text, effective_date date,
            title text NOT NULL, boxed_warning text, warnings_and_precautions text,
            contraindications text, drug_interactions text, indications_and_usage text,
            dosage_and_administration text,
        """,
        "recalls": """
            recall_number text, event_id text, product_description text NOT NULL,
            reason_for_recall text NOT NULL, classification text, reported_status text,
            recalling_firm text, recall_initiation_date date, report_date date,
            distribution_pattern text, lot_information text,
        """,
        "adverse_events": """
            report_version text, received_date date, last_received_date date,
            serious boolean, seriousness_details jsonb NOT NULL DEFAULT '{}',
            reported_drugs jsonb NOT NULL DEFAULT '[]',
            reactions text[] NOT NULL DEFAULT '{}', country text,
        """,
        "safety_communications": """
            title text NOT NULL, communication_type text NOT NULL,
            published_date date, body_text text NOT NULL,
        """,
    }
    for table, fields in columns.items():
        op.execute(f"CREATE TABLE pharma.{table} (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), {fields} {provenance})")
        op.execute(f"CREATE INDEX ON pharma.{table} (ingestion_run_id)")
    for table, target, key in [
        ("drug_label_links", "drug_labels", "drug_label_id"),
        ("drug_recall_links", "recalls", "recall_id"),
        ("drug_adverse_event_links", "adverse_events", "adverse_event_id"),
        ("drug_safety_communication_links", "safety_communications", "safety_communication_id"),
    ]:
        op.execute(f"""CREATE TABLE pharma.{table} (
            drug_id uuid NOT NULL REFERENCES pharma.drugs(id) ON DELETE CASCADE,
            {key} uuid NOT NULL REFERENCES pharma.{target}(id) ON DELETE CASCADE,
            match_method text NOT NULL CHECK (match_method IN ('rxcui', 'ndc', 'name')),
            matched_value text NOT NULL,
            PRIMARY KEY (drug_id, {key})
        )""")
        op.execute(f"CREATE INDEX ON pharma.{table} ({key})")
    op.execute("CREATE INDEX ON pharma.drugs (normalized_generic_name)")
    # RxCUIs can legitimately identify several marketed NDC products.
    op.execute("CREATE INDEX ON pharma.drugs (rxcui) WHERE rxcui IS NOT NULL")
    for field in ("normalized_names", "product_ndcs", "package_ndcs"):
        op.execute(f"CREATE INDEX ON pharma.drugs USING gin ({field})")
    for table, field in [("recalls", "report_date"), ("adverse_events", "received_date"),
                         ("safety_communications", "published_date"), ("drug_labels", "effective_date")]:
        op.execute(f"CREATE INDEX ON pharma.{table} ({field})")
    op.execute("CREATE INDEX ON pharma.drug_labels (label_set_id, effective_date DESC)")
    op.execute("CREATE INDEX ON pharma.ingestion_runs (source, started_at DESC)")


def downgrade() -> None:
    for table in ("drug_safety_communication_links", "drug_adverse_event_links",
                  "drug_recall_links", "drug_label_links", "safety_communications",
                  "adverse_events", "recalls", "drug_labels", "drugs", "ingestion_runs"):
        op.execute(f"DROP TABLE pharma.{table}")
    op.execute("DROP SCHEMA pharma")
