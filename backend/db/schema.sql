-- Dav AI database schema
-- Phase 1: source registry and audit events
-- No personal health information should be stored in this schema.

create table if not exists source_registry (
    source_id text primary key,
    source_name text not null,
    endpoint text not null,
    module text not null,
    description text not null,
    update_cadence text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists audit_events (
    audit_id uuid primary key,
    module text not null,
    source_id text not null references source_registry(source_id),
    source_name text not null,
    endpoint text not null,
    query text not null,
    query_params jsonb not null default '{}'::jsonb,
    retrieval_timestamp timestamptz not null,
    upstream_status text not null,
    record_count integer not null default 0,
    transform_version text not null,
    score_version text,
    disclaimer_version text not null,
    error_message text,
    created_at timestamptz not null default now(),

    constraint audit_events_upstream_status_check
        check (upstream_status in ('success', 'empty', 'error')),

    constraint audit_events_record_count_check
        check (record_count >= 0)
);

create index if not exists idx_audit_events_source_id
    on audit_events(source_id);

create index if not exists idx_audit_events_module
    on audit_events(module);

create index if not exists idx_audit_events_created_at
    on audit_events(created_at desc);

create index if not exists idx_audit_events_upstream_status
    on audit_events(upstream_status);

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
    ),
    (
        'rxnorm_rxnav_api',
        'RxNorm/RxNav API',
        'https://rxnav.nlm.nih.gov/REST',
        'RealWorldSafety',
        'U.S. National Library of Medicine RxNorm drug terminology source used for drug-name normalization and RXCUI reference lookup.',
        'NLM RxNorm releases and RxNav API updates'
    ),
    (
        'dailymed_spl_api',
        'DailyMed SPL API',
        'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json',
        'RealWorldSafety',
        'U.S. National Library of Medicine DailyMed Structured Product Label source for official drug label references.',
        'DailyMed SPL label updates'
    ),
    (
        'openfda_drug_label',
        'openFDA Drug Label API',
        'https://api.fda.gov/drug/label.json',
        'RealWorldSafety',
        'Official openFDA drug label records for active ingredients, warnings, dosage, and usage sections.',
        'Source-dependent FDA drug label updates'
    ),
    (
        'openfda_device_enforcement',
        'openFDA Device Enforcement API',
        'https://api.fda.gov/device/enforcement.json',
        'RealWorldSafety',
        'FDA medical device recall enforcement records from openFDA.',
        'Source-dependent FDA device enforcement updates'
    ),
    (
        'openfda_device_event',
        'openFDA Device Event API',
        'https://api.fda.gov/device/event.json',
        'RealWorldSafety',
        'FDA medical device adverse-event reports from openFDA. These are signal reports, not recalls or proof of causation.',
        'Source-dependent FDA device event updates'
    ),
    (
        'openfda_cosmetic_event',
        'openFDA Cosmetic Event API',
        'https://api.fda.gov/cosmetic/event.json',
        'CosmeticSignal',
        'Cosmetic adverse-event reports from openFDA for skincare, makeup, hair, fragrance, and related products.',
        'Source-dependent FDA cosmetic event updates'
    ),
    (
        'openfda_food_enforcement',
        'openFDA Food Enforcement API',
        'https://api.fda.gov/food/enforcement.json',
        'FoodRadar',
        'Food, supplement, grocery, and packaged-food recall enforcement records from openFDA.',
        'Source-dependent FDA updates'
    ),
    (
        'usda_fsis_recall',
        'USDA FSIS Recall API',
        'https://www.fsis.usda.gov/fsis/api/recall/v/1',
        'FoodRadar',
        'Meat, poultry, egg-product recall and public-health-alert records from USDA FSIS.',
        'Real-time FSIS recall and public health alert updates'
    ),
    (
        'foodradar_multi_source',
        'FoodRadar Multi-Source Recall Search',
        'https://api.fda.gov/food/enforcement.json + https://www.fsis.usda.gov/fsis/api/recall/v/1',
        'FoodRadar',
        'Aggregate FoodRadar workflow combining openFDA Food Enforcement and USDA FSIS recall/public-health-alert records.',
        'Source-dependent FDA updates plus FSIS recall/public-health-alert updates'
    ),
    (
        'fda_recalls_market_withdrawals_safety_alerts',
        'FDA Recalls, Market Withdrawals & Safety Alerts',
        'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
        'RealWorldSafety',
        'Public FDA recall, market withdrawal, and safety alert notices visible on FDA.gov, including notices that may not appear in openFDA enforcement APIs.',
        'FDA public notice page updates as recalls, market withdrawals, and safety alerts are posted'
    ),
    (
        'cpsc_recalls_api',
        'CPSC Recalls API',
        'https://www.saferproducts.gov/RestWebServices/Recall',
        'RealWorldSafety',
        'Consumer Product Safety Commission recall records for home goods, electronics, batteries, scooters, toys, baby products, furniture, appliances, and other consumer products.',
        'CPSC recall API updates as public recalls are published'
    ),
    (
        'nhtsa_vpic_vin_decoder_api',
        'NHTSA vPIC VIN Decoder API',
        'https://vpic.nhtsa.dot.gov/api/',
        'RealWorldSafety',
        'NHTSA vPIC vehicle decoder used to turn VIN input into make, model, and model year before recall lookup.',
        'NHTSA vPIC public API updates as vehicle product information is refreshed'
    ),
    (
        'nhtsa_recalls_api_datasets',
        'NHTSA Recalls API / datasets',
        'https://api.nhtsa.gov/recalls/recallsByVehicle',
        'RealWorldSafety',
        'NHTSA vehicle recall records by make, model, and model year for vehicle safety checks.',
        'NHTSA recall data updates as campaigns and safety notices are published'
    ),
    (
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
    updated_at = now();

-- Saved Monitors v2
-- Stores repeatable public-data monitor definitions and latest manual run state.
-- No personal health information should be stored in this table.

create table if not exists saved_monitors (
    id uuid primary key,
    name text not null,
    query text not null,
    module text not null,
    created_at timestamptz not null default now(),
    last_checked_at timestamptz,
    latest_audit_id uuid,
    latest_score integer,
    previous_score integer,
    latest_record_count integer,
    previous_record_count integer,
    status text not null default 'not_checked',
    refresh_enabled boolean not null default false,
    refresh_interval_minutes integer,
    next_run_at timestamptz,
    last_scheduled_run_at timestamptz,
    last_scheduled_status text,

    constraint saved_monitors_module_check
        check (module in ('recallradar', 'drugsignal', 'foodradar', 'regional_health_pulse')),

    constraint saved_monitors_status_check
        check (status in ('not_checked', 'checked', 'error')),

    constraint saved_monitors_latest_score_check
        check (latest_score is null or latest_score >= 0),

    constraint saved_monitors_previous_score_check
        check (previous_score is null or previous_score >= 0),

    constraint saved_monitors_latest_record_count_check
        check (latest_record_count is null or latest_record_count >= 0),

    constraint saved_monitors_previous_record_count_check
        check (previous_record_count is null or previous_record_count >= 0),

    constraint saved_monitors_refresh_interval_check
        check (refresh_interval_minutes is null or refresh_interval_minutes > 0),

    constraint saved_monitors_last_scheduled_status_check
        check (
            last_scheduled_status is null
            or last_scheduled_status in ('success', 'error', 'skipped')
        )
);

create index if not exists idx_saved_monitors_module
    on saved_monitors(module);

create index if not exists idx_saved_monitors_status
    on saved_monitors(status);

create index if not exists idx_saved_monitors_created_at
    on saved_monitors(created_at desc);

create index if not exists idx_saved_monitors_last_checked_at
    on saved_monitors(last_checked_at desc);

create index if not exists idx_saved_monitors_due_refresh
    on saved_monitors(refresh_enabled, next_run_at);

-- Saved Monitor Run History v2.2
-- Stores one row for each manual or scheduled saved monitor run.
-- This is run-history persistence and does not store raw source payloads.

create table if not exists saved_monitor_runs (
    run_id uuid primary key,
    monitor_id uuid not null references saved_monitors(id) on delete cascade,
    module text not null,
    query text not null,
    status text not null,
    record_count integer,
    score integer,
    score_label text,
    audit_id uuid,
    created_at timestamptz not null default now(),
    error_message text,

    constraint saved_monitor_runs_module_check
        check (module in ('recallradar', 'drugsignal', 'foodradar', 'regional_health_pulse')),

    constraint saved_monitor_runs_status_check
        check (status in ('success', 'error')),

    constraint saved_monitor_runs_record_count_check
        check (record_count is null or record_count >= 0),

    constraint saved_monitor_runs_score_check
        check (score is null or score >= 0)
);

create index if not exists idx_saved_monitor_runs_monitor_id_created_at
    on saved_monitor_runs(monitor_id, created_at desc);

create index if not exists idx_saved_monitor_runs_status
    on saved_monitor_runs(status);

-- Scheduler Locks v2.4
-- Stores durable job leases for scheduled backend jobs.
-- This prevents overlapping scheduled refresh jobs across processes,
-- deployments, restarts, or production Cron overlap.

create table if not exists scheduler_locks (
    lock_name text primary key,
    locked_by text not null,
    locked_until timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_scheduler_locks_locked_until
    on scheduler_locks(locked_until);

-- Source Pulls and Raw Source Snapshots v2.5
-- Stores reproducible public-source retrieval records and raw openFDA payloads.
-- This stores public API payloads only; no PHI or user medical history should be stored.

create table if not exists source_pulls (
    pull_id uuid primary key,
    audit_id uuid references audit_events(audit_id) on delete set null,
    source_id text not null references source_registry(source_id),
    source_name text not null,
    endpoint text not null,
    query text not null,
    query_params jsonb not null default '{}'::jsonb,
    retrieval_timestamp timestamptz not null,
    upstream_status text not null,
    record_count integer not null default 0,
    payload_hash text not null,
    transform_version text not null,
    created_at timestamptz not null default now(),

    constraint source_pulls_upstream_status_check
        check (upstream_status in ('success', 'empty', 'error')),

    constraint source_pulls_record_count_check
        check (record_count >= 0)
);

create table if not exists raw_source_snapshots (
    snapshot_id uuid primary key,
    pull_id uuid not null references source_pulls(pull_id) on delete cascade,
    raw_payload jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_source_pulls_audit_id
    on source_pulls(audit_id);

create index if not exists idx_source_pulls_source_id_created_at
    on source_pulls(source_id, created_at desc);

create index if not exists idx_source_pulls_upstream_status
    on source_pulls(upstream_status);

create index if not exists idx_source_pulls_payload_hash
    on source_pulls(payload_hash);

create index if not exists idx_raw_source_snapshots_pull_id
    on raw_source_snapshots(pull_id);
