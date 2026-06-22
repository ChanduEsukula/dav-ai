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
            "rxnorm_rxnav_api",
            "dailymed_spl_api",
            "openfda_device_enforcement",
        "openfda_cosmetic_event",
        "openfda_food_enforcement",
        "usda_fsis_recall",
        "foodradar_multi_source",
        "fda_recalls_market_withdrawals_safety_alerts",
        "cpsc_recalls_api",
        "nhtsa_vpic_vin_decoder_api",
        "nhtsa_recalls_api_datasets",
        "regional_health_pulse_demo",
    }
    assert modules == {
        "RecallRadar",
        "DrugSignal",
        "CosmeticSignal",
        "FoodRadar",
        "RealWorldSafety",
        "RegionalHealthPulse",
    }


def test_schema_snapshot_includes_regional_health_source_and_monitor_constraints():
    schema_sql = SCHEMA_PATH.read_text()

    assert "'regional_health_pulse_demo'" in schema_sql
    assert "'Regional Health Pulse MVP scaffold'" in schema_sql
    assert "saved_monitors_module_check" in schema_sql
    assert "saved_monitor_runs_module_check" in schema_sql
    assert "check (module in ('recallradar', 'drugsignal', 'foodradar', 'regional_health_pulse'))" in schema_sql


def test_regional_health_alignment_migration_covers_seed_and_constraints():
    migration_source = MIGRATION_PATH.read_text()

    assert 'revision = "20260527_0007"' in migration_source
    assert 'down_revision = "20260521_0006"' in migration_source
    assert "'regional_health_pulse_demo'" in migration_source
    assert "drop constraint if exists saved_monitors_module_check" in migration_source
    assert "drop constraint if exists saved_monitor_runs_module_check" in migration_source
    assert "check (module in ('recallradar', 'drugsignal', 'foodradar', 'regional_health_pulse'))" in migration_source


def test_runtime_sources_are_seeded_in_database_schema():
    schema_sql = SCHEMA_PATH.read_text()

    for source in REGISTERED_SOURCES:
        assert source["source_id"] in schema_sql
        assert source["source_name"] in schema_sql
        assert source["endpoint"] in schema_sql
        assert source["module"] in schema_sql


def test_foodradar_audit_source_id_is_registered_and_seeded():
    schema_sql = SCHEMA_PATH.read_text()
    registered_source_ids = {source["source_id"] for source in REGISTERED_SOURCES}

    assert "foodradar_multi_source" in registered_source_ids
    assert "foodradar_multi_source" in schema_sql


def test_no_duplicate_registered_source_ids():
    source_ids = [source["source_id"] for source in REGISTERED_SOURCES]

    assert len(source_ids) == len(set(source_ids))


def test_foodradar_saved_monitor_constraint_migration_exists():
    migration_source = (
        REPO_ROOT
        / "backend"
        / "migrations"
        / "versions"
        / "20260605_0008_add_foodradar_saved_monitor_constraints.py"
    ).read_text()

    assert 'revision = "20260605_0008"' in migration_source
    assert 'down_revision = "20260527_0007"' in migration_source
    assert "drop constraint if exists saved_monitors_module_check" in migration_source
    assert "drop constraint if exists saved_monitor_runs_module_check" in migration_source
    assert "check (module in ('recallradar', 'drugsignal', 'foodradar', 'regional_health_pulse'))" in migration_source

def test_everyday_safety_source_seed_migration_exists():
    migration_source = (
        REPO_ROOT
        / "backend"
        / "migrations"
        / "versions"
        / "20260608_0009_seed_everyday_safety_sources.py"
    ).read_text()

    assert 'revision = "20260608_0009"' in migration_source
    assert 'down_revision = "20260605_0008"' in migration_source

    for source_id in {
        "openfda_cosmetic_event",
        "openfda_food_enforcement",
        "usda_fsis_recall",
        "foodradar_multi_source",
    }:
        assert source_id in migration_source

    assert "on conflict (source_id) do update set" in migration_source


def test_real_world_safety_source_seed_migration_exists():
    migration_source = (
        REPO_ROOT
        / "backend"
        / "migrations"
        / "versions"
        / "20260622_0011_seed_real_world_safety_sources.py"
    ).read_text()

    assert 'revision = "20260622_0011"' in migration_source
    assert 'down_revision = "20260616_0010"' in migration_source

    for source_id in {
        "fda_recalls_market_withdrawals_safety_alerts",
        "cpsc_recalls_api",
        "nhtsa_vpic_vin_decoder_api",
        "nhtsa_recalls_api_datasets",
    }:
        assert source_id in migration_source

    assert "on conflict (source_id) do update set" in migration_source
