# Dav AI Platform Modules and OutbreakSignal Plan

## Purpose

Dav AI is evolving from a narrow FDA recall/adverse-event prototype into a broader public health and safety intelligence platform.

The product should stay focused on trusted public data, source transparency, auditability, repeatable monitoring, and responsible AI guardrails.

This document organizes the current implemented modules and defines how a future disease-outbreak module should fit into the existing architecture without turning the product into an unsafe medical chatbot or personal health-risk predictor.

## Platform Positioning

Dav AI is a public health and safety intelligence platform that turns trusted public datasets into source-aware, explainable, auditable review workflows.

Dav AI does not diagnose, prescribe, claim causation, predict personal medical risk, or replace FDA, CDC, HHS, clinicians, pharmacists, public-health authorities, or emergency services.

## Current Implemented Modules

### RecallRadar

Searches public FDA/openFDA drug enforcement recall records and converts them into structured review cards with source metadata, audit details, transparent scoring, and role-based safety briefings.

### DrugSignal

Searches public openFDA Drug Event / FAERS-style adverse-event reporting records and summarizes reporting patterns with strong causation disclaimers.

### Safety Briefing Engine

Creates deterministic role-based summaries from structured public-data results. It currently uses structured facts only and does not use an LLM for the MVP.

### Audit History and Source Provenance

Records public-data searches, source metadata, query parameters, retrieval timestamps, record counts, transform versions, score versions, request context, source pulls, and raw public payload hashes.

### Saved Monitors

Allows repeatable public-data searches, manual runs, run history, latest/previous comparison, change indicators, related audit links, and a backend scheduled-refresh foundation.

### System Status and Data Quality

Provides lightweight operational transparency into backend health, database configuration, audit readability, registered sources, recent audit activity, and upstream status counts.

## Planned Module: Regional Health Pulse / OutbreakSignal

Regional Health Pulse, also called OutbreakSignal, would extend Dav AI from FDA/openFDA safety signals into public-health and outbreak-awareness signals from trusted public datasets.

Use **Regional Health Pulse** in the app navigation because it sounds broader, safer, and less alarmist. Use **OutbreakSignal** internally if needed.

## Safe Scope

Regional Health Pulse should answer:

- What public-health signal changed in this region?
- What does the trusted public source say?
- When was the public source retrieved?
- Is the available public-data trend increasing, stable, decreasing, or insufficient?
- What should a clinic, pharmacy, university health center, or public-health reviewer verify next?

It should not answer:

- Am I personally at risk?
- Do I have this disease?
- Should I take medication?
- Is this an emergency?
- Will an outbreak happen tomorrow?

## Candidate Public Data Sources

Potential sources:

- CDC open data datasets.
- HealthData.gov datasets.
- HHS public hospital utilization datasets.
- CDC respiratory illness activity datasets, if accessible through stable public endpoints.
- Public state or county health datasets, only if source terms and update cadence are clear.

Each source must be evaluated for public accessibility, stable API access, update cadence, geographic granularity, data dictionary quality, safe interpretation, source timestamps, and auditability.

## Regional Health Pulse v1 MVP

The smallest useful version should be:

1. User selects or searches a region.
2. User selects a public-health category.
3. Backend fetches one trusted public dataset.
4. Backend normalizes the public records into a small response schema.
5. Backend stores an audit event and source pull.
6. Frontend shows region, category, latest value or signal label, trend label, source name, retrieval timestamp, limitations, and disclaimer.
7. Briefing Engine generates a role-based public-health review briefing.
8. Later, Saved Monitors can support repeatable regional checks.

## Proposed Backend Architecture

Possible backend additions:

```text
backend/app/routes/regional_health.py
backend/app/services/search_workflows/regional_health_search.py
backend/app/services/cdc_client.py
backend/app/services/hhs_client.py
backend/app/schemas/regional_health.py
backend/app/scoring/regional_health_signal.py
backend/tests/test_regional_health_route.py
backend/tests/test_regional_health_signal.py