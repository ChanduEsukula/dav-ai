from pathlib import Path

from app.sources.registry import REGISTERED_SOURCES


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "backend" / "db" / "schema.sql"
MIGRATION_PATH = (
    REPO_ROOT
    / "backend"
    / "migrations"
    / "versions"
    / "20260527_0007_align_regional_health_source_and_monitor_constraints.py"
)


def test_registered_sources_include_current_public_source_surfaces():
    source_ids = {source["source_id"] for source in REGISTERED_SOURCES}
    modules = {source["module"] for source in REGISTERED_SOURCES}

    assert source_ids == {
        "openfda_drug_enforcement",
        "openfda_drug_event",
        "regional_health_pulse_demo",
    }
    assert modules == {
        "RecallRadar",
        "DrugSignal",
        "RegionalHealthPulse",
    }


def test_schema_snapshot_includes_regional_health_source_and_monitor_constraints():
    schema_sql = SCHEMA_PATH.read_text()

    assert "'regional_health_pulse_demo'" in schema_sql
    assert "'Regional Health Pulse MVP scaffold'" in schema_sql
    assert "saved_monitors_module_check" in schema_sql
    assert "saved_monitor_runs_module_check" in schema_sql
    assert "check (module in ('recallradar', 'drugsignal', 'regional_health_pulse'))" in schema_sql


def test_regional_health_alignment_migration_covers_seed_and_constraints():
    migration_source = MIGRATION_PATH.read_text()

    assert 'revision = "20260527_0007"' in migration_source
    assert 'down_revision = "20260521_0006"' in migration_source
    assert "'regional_health_pulse_demo'" in migration_source
    assert "drop constraint if exists saved_monitors_module_check" in migration_source
    assert "drop constraint if exists saved_monitor_runs_module_check" in migration_source
    assert "check (module in ('recallradar', 'drugsignal', 'regional_health_pulse'))" in migration_source