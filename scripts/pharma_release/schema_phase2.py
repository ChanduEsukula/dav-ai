"""Additive identity columns on a fresh Phase 1 schema; no existing DB migration."""
from . import SCHEMA_VERSION
from .schema import create_schema, schema_sql

PHASE2_SCHEMA_VERSION = SCHEMA_VERSION + ".phase2-identity1"
EXTENSION_SQL = """
ALTER TABLE products ADD COLUMN application_number TEXT;
ALTER TABLE products ADD COLUMN dosage_form TEXT;
ALTER TABLE products ADD COLUMN routes_json TEXT CHECK(routes_json IS NULL OR (json_valid(routes_json) AND json_type(routes_json)='array'));
ALTER TABLE products ADD COLUMN finished INTEGER CHECK(finished IS NULL OR finished IN (0,1));
ALTER TABLE products ADD COLUMN consumer_classification TEXT NOT NULL DEFAULT 'REGULATORY_RESEARCH_ONLY'
  CHECK(consumer_classification IN ('NORMAL_CONSUMER_HUMAN_PRODUCT','SPECIAL_REGULATORY_CATEGORY_HUMAN_PRODUCT','REGULATORY_RESEARCH_ONLY','UNRESOLVED_IDENTITY'));
PRAGMA user_version=2;
"""


def create_phase2_schema(connection):
    create_schema(connection)
    connection.executescript("BEGIN;\n" + EXTENSION_SQL + "\nCOMMIT;")


def phase2_schema_sql():
    return schema_sql() + "\n-- " + PHASE2_SCHEMA_VERSION + "\n" + EXTENSION_SQL
