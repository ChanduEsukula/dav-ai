# Dav AI Architecture Overview — June 2026

## Purpose

Dav AI is a public-data safety review workspace. It helps users search FDA and USDA public records, normalize common search terms, review source evidence, preserve audit metadata, and generate bounded reports.

The system is intentionally scoped as a public-record verification tool. It does not provide medical advice, determine whether a product is safe, prove causation, or replace official FDA/USDA notices.

## High-Level Architecture

```text
User
  |
  v
React + TypeScript Frontend
  |
  |-- Guided public-record search
  |-- Pharmacy Safety
  |-- Food Safety
  |-- Cosmetic Safety
  |-- Saved Monitors
  |-- Audit History
  |-- Sources / System Status
  |-- PDF Report Intake
  |
  v
FastAPI Backend
  |
  |-- Search workflows
  |-- Query normalization
  |-- Deterministic review scoring
  |-- Source clients
  |-- Audit and provenance services
  |-- Saved monitor services
  |-- PDF report generation
  |
  v
Public Data Sources + PostgreSQL
  |
  |-- FDA / openFDA public records
  |-- USDA / FSIS public records
  |-- Audit events
  |-- Source pulls
  |-- Payload hashes
  |-- Saved monitor history
```

## Frontend

The frontend is built with React, TypeScript, Vite, Axios, Vitest, Testing Library, and Playwright.

The current canonical product workflows are:

- Pharmacy Safety
- Food Safety
- Cosmetic Safety

The homepage provides guided public-record search and routes users to the most relevant workflow. Query normalization and suggestions help users recover from common misspellings, plural forms, and no-space product terms such as:

```text
xanex         -> xanax
strawberries  -> strawberry
hairdye       -> hair dye
proteinpowder -> protein powder
```

The frontend preserves both the normalized query and the original user query when relevant, so the UI can show honest messages such as:

> Showing results for “strawberry” based on your search “strawberries.”

## Backend

The backend is built with FastAPI, Pydantic, PostgreSQL, Alembic, and service-oriented workflow modules.

Major backend responsibilities include:

- validating incoming search requests
- normalizing bounded query aliases
- calling public FDA/openFDA and USDA source clients
- mapping source responses into typed application schemas
- calculating deterministic review signals
- creating audit events and source-pull metadata
- generating PDF reports
- supporting Saved Monitor workflows

The backend does not use production ML or LLM inference to make safety decisions. Current scoring is deterministic, explainable, and versioned.

## Public Data Workflows

### Pharmacy Safety

Pharmacy Safety handles drug recall-style records and adverse-event reporting patterns.

Important boundaries:

- adverse-event reports do not prove causation
- result counts do not represent incidence
- review signals are not medical-risk scores
- users must verify exact label, strength, manufacturer, NDC, lot, and official source details

### Food Safety

Food Safety reviews public food and supplement safety records from supported public sources.

Important boundaries:

- source data may be incomplete or delayed
- result matches do not prove a user’s exact package is affected
- users must compare brand, package, lot/code, establishment number, and official recall notices

### Cosmetic Safety

Cosmetic Safety reviews public cosmetic-event reports and reaction patterns.

Important boundaries:

- public reports can be incomplete, duplicated, delayed, or influenced by reporting behavior
- returned reports do not prove product defect or causation
- zero returned reports are shown as not assessable rather than as a safety guarantee

## Query Normalization and Suggestions

Dav AI uses bounded alias normalization instead of broad uncontrolled fuzzy matching.

This approach was chosen because public safety search needs predictable, testable behavior. The system should help users with common inputs without silently rewriting every query.

Examples include:

- pharmacy misspellings and variants
- food singular/plural aliases
- cosmetic no-space terms
- common product phrase normalization

The app preserves the original query and displays normalized-query messages when the submitted query changes.

## Provenance and Audit Model

The provenance layer is one of the strongest parts of Dav AI.

Search workflows can record:

- module/workflow name
- original and normalized query
- source name
- retrieval timestamp
- request metadata
- transform version
- score version
- upstream source status
- source-pull metadata
- raw public-source snapshot references
- stable SHA-256 payload hashes

This allows reviewers to trace how a result was produced and what source context was available at retrieval time.

## Saved Monitors

Saved Monitors allow repeatable public-record checks with stored run history and comparison metadata.

Current monitor support is intentionally limited to workflows with backend and persistence parity. Unsupported workflows are hidden from monitor creation until database constraints, manual execution, and tests are complete.

Saved Monitors are not production alerting. They are a portfolio-grade foundation for repeatable checks.

## Reports

Dav AI can generate bounded PDF reports using supported public-record workflows.

Reports include source context and limitations, but they are not regulatory documents, clinical documents, or safety certificates.

The report system is useful for demonstrating how search results, source metadata, audit context, and safety boundaries can be packaged for review.

## ProductScan OCR v2 Plan

ProductScan OCR v2 has partially progressed from planning into an experimental frontend-only intake scaffold. Production OCR is not currently implemented.

Current experimental scope:

```text
Local label image upload preview
  -> optional browser-side OCR with editable text
  -> deterministic candidate identifiers
  -> user confirmation and workflow choice
  -> route to Pharmacy Safety, Food Safety, or Cosmetic Safety
```

ProductScan does not determine whether a product is safe or unsafe. OCR only assists with label-text extraction and routing. Dav AI does not store uploaded ProductScan images, does not run backend/provider OCR, and does not use vector DB, RAG, LLM analysis, or OCR output for safety decisioning. Deep learning experiments should remain offline until evaluation, safety boundaries, and monitoring are defined.

## Testing Strategy

Dav AI uses layered testing:

- backend route tests
- scoring and normalization tests
- repository and persistence tests
- frontend component tests
- accessibility-oriented UI behavior tests
- Playwright smoke tests
- lint and TypeScript checks
- production build validation

Recent validation checkpoints include:

- Backend pytest: 488 passed
- Frontend tests: 282 passed
- ESLint: passed
- TypeScript/Vite build: passed
- Playwright Chromium smoke tests: 3 passed
- `git diff --check`: passed

## Current Production-Readiness Boundaries

Dav AI is portfolio-grade, not production-ready for uncontrolled public use.

Missing production features include:

- production authentication
- authorization / RBAC
- durable user ownership policies
- tenant isolation
- rate limiting
- abuse protection
- retention and deletion policy
- PHI handling controls
- production alert delivery
- pagination and caching at scale
- database connection pooling
- observability, SLOs, and incident response
- independent safety review

## Engineering Decisions

Key decisions:

1. Use deterministic review signals instead of production ML for safety-sensitive public data.
2. Preserve source provenance instead of hiding uncertainty.
3. Use bounded query normalization instead of uncontrolled fuzzy matching.
4. Keep ProductScan OCR experimental and user-reviewed; keep backend/provider OCR and deep learning out of the stable safety workflows.
5. Present limitations directly in the UI and reports.
6. Stabilize canonical workflows before adding more modules.

## Portfolio Value

Dav AI demonstrates:

- full-stack product ownership
- React and TypeScript frontend engineering
- FastAPI backend design
- public API integration
- query normalization and UX polish
- source provenance and audit trails
- deterministic scoring
- PDF generation
- database-backed monitor workflows
- responsible AI/product boundaries
- test automation and CI discipline

The strongest engineering story is not that Dav AI “uses AI everywhere.” The strongest story is that it uses careful public-data workflows, explainable logic, provenance, and honest limitations to reduce user misunderstanding.
