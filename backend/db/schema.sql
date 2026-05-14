-- MedTrek AI database schema
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

    constraint saved_monitors_module_check
        check (module in ('recallradar', 'drugsignal')),

    constraint saved_monitors_status_check
        check (status in ('not_checked', 'checked', 'error')),

    constraint saved_monitors_latest_score_check
        check (latest_score is null or latest_score >= 0),

    constraint saved_monitors_previous_score_check
        check (previous_score is null or previous_score >= 0),

    constraint saved_monitors_latest_record_count_check
        check (latest_record_count is null or latest_record_count >= 0),

    constraint saved_monitors_previous_record_count_check
        check (previous_record_count is null or previous_record_count >= 0)
);

create index if not exists idx_saved_monitors_module
    on saved_monitors(module);

create index if not exists idx_saved_monitors_status
    on saved_monitors(status);

create index if not exists idx_saved_monitors_created_at
    on saved_monitors(created_at desc);

create index if not exists idx_saved_monitors_last_checked_at
    on saved_monitors(last_checked_at desc);

-- Saved Monitor Run History v2.2
-- Stores one row for each manual saved monitor run.
-- This is not scheduled monitoring and does not store raw source payloads.

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
        check (module in ('recallradar', 'drugsignal')),

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
