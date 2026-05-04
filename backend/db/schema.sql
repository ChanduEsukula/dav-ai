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