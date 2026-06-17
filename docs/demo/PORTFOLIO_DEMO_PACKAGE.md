# Dav AI Portfolio Demo Package — June 2026

## Stable demo version

- Recommended tag: `demo-polished-query-june-2026`
- Current main checkpoint: `7fe23d3`
- ProductScan planning checkpoint: `productscan-ocr-v2-plan-june-2026`
- ProductScan experimental intake checkpoint: browser-side OCR scaffold

## One-line description

Dav AI is a React, TypeScript, FastAPI, and PostgreSQL public-data safety review workspace that helps users search FDA/USDA records, normalize queries, review source evidence, and preserve provenance through audit metadata.

## Demo scope

The demo focuses on:

1. Guided public-record search
2. Pharmacy Safety
3. Food Safety
4. Cosmetic Safety
5. Query normalization and suggestions
6. Audit and source provenance
7. Saved Monitors
8. Experimental ProductScan browser-side OCR intake

## What Dav AI is not

- Not medical advice
- Not a clinical system
- Not a product-safety verdict engine
- Not FDA-approved
- Not production-ready for uncontrolled public use
- Not a deployed ML prediction system

## Recommended demo queries

- Pharmacy: `xanex` → normalized to `xanax`
- Food: `strawberries` → normalized to `strawberry`
- Cosmetic: `hairdye` → normalized to `hair dye`
- No-space: `proteinpowder` → normalized to `protein powder`

## Three-minute demo flow

1. Start on Home and explain public-record verification.
2. Show the guided search and suggestions.
3. Search `xanex` and route to Pharmacy Safety.
4. Search `strawberries` and show Food Safety normalization.
5. Search `hairdye` and show Cosmetic Safety normalization.
6. Open Audit and Sources to show provenance.
7. Mention Saved Monitors as repeatable checks.
8. Mention ProductScan as experimental browser-side OCR-assisted label extraction, not safety prediction.

## Strongest engineering points

- Source-aware public-data workflows
- Deterministic review signals
- Query normalization and accessible suggestions
- Audit events and provenance metadata
- Source registry and freshness status
- Saved monitor history
- PDF report generation
- 300+ backend tests and 180+ frontend tests
- Responsible AI boundaries

## Known limitations

- No authentication or ownership yet
- No production alert delivery
- No clinical advice
- No safety guarantee
- No complete UPC/NDC/lot matching
- ProductScan browser-side OCR is experimental and user-reviewed; no backend OCR, provider OCR, image storage, or production OCR pipeline yet
- No production ML pipeline
- Source data may be incomplete, delayed, duplicated, or difficult to interpret

## Screenshot checklist

- Home
- Guided search suggestions
- Pharmacy Safety result
- Food Safety normalization result
- Cosmetic Safety result
- Audit detail
- Sources page
- Saved Monitors
- System status
- Experimental ProductScan intake page and limitations

## Interview framing

Dav AI is valuable because it makes fragmented public safety records easier to search, interpret cautiously, and trace back to source evidence. The project intentionally uses deterministic logic and explicit limitations instead of pretending to make clinical or product-safety decisions.

## Validation Checkpoint - June 17, 2026

This checkpoint was verified on branch `chore/demo-hardening-june-2026`.

Validation commands run:

    PYTHONPATH=backend pytest backend/tests
    cd frontend
    npm test
    npm run lint
    npm run build

Results:

- Backend tests: 345 passed
- Frontend tests: 224 passed
- Total automated tests: 569 passed
- Frontend lint: passed
- Frontend production build: passed

Notes:

- Backend tests must be run with `PYTHONPATH=backend` from the repository root so imports such as `app.main` and `ml_experiments` resolve correctly.
- ProductScan OCR, docs semantic preview, saved monitors, reports, audit history, and source-backed safety workflows are demo-ready prototype features.
- Dav AI remains a public-record review workspace, not medical advice, clinical decision support, or a product-safety verdict system.

## Deployed Smoke Check - June 17, 2026

After PR #123 was merged, the deployment was checked for portfolio demo readiness.

Manual smoke areas:

- Home page
- Guided safety search
- Pharmacy Safety
- Food Safety
- Cosmetic Safety
- Sources
- System Status
- Saved Monitors
- Help Docs Search
- ProductScan intake

Result: deployment smoke-ready for portfolio demo.

Notes:

- This smoke check verifies portfolio/demo readiness, not production healthcare readiness.
- Dav AI remains a public-record review workspace and does not provide medical advice, clinical decision support, or product-safety verdicts.
