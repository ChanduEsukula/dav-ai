# Dav AI Portfolio Demo Package — Public Safety v1

## Stable demo version

Recommended current checkpoint:

- `realworld-safety-focused-nav-v1`
- `realworld-safety-readme-centerpiece-v1`
- `realworld-safety-registry-alignment-v1`
- `realworld-safety-ui-clean-v1`

Current flagship workflow: **Public Safety Search**

## One-line description

Dav AI is a full-stack public safety intelligence platform that helps users search fragmented U.S. public recall, enforcement, label, reference, vehicle, device, food, drug, cosmetic, and consumer-product records while preserving source provenance and avoiding unsupported safety claims.

## Best portfolio positioning

Use this positioning for GitHub, LinkedIn, resume, and interviews:

> Dav AI is a source-aware public safety intelligence and recall verification platform.

Do not lead with “chatbot,” “medical AI,” “outbreak detector,” or “OCR scanner.” The strongest engineering story is official/public data integration, source roles, query understanding, provenance, and careful safety boundaries.

## Demo scope

The short demo should focus on:

1. Home page with Public Safety Search as the primary path
2. Public Safety Search result for a consumer product recall-style query
3. Public Safety Search result for a drug brand/generic or typo query
4. Query understanding and expansion explanation
5. Reference-versus-recall distinction
6. Official source links
7. Audit / Sources briefly to show provenance and registered sources

Use Pharmacy, Food, Cosmetic, Saved Monitors, and ProductScan only as secondary breadth examples.

## What Dav AI is not

- Not medical advice
- Not legal advice
- Not clinical decision support
- Not a product-safety verdict engine
- Not proof that a product is safe or unsafe
- Not proof of adverse-event causation
- Not an exhaustive recall database
- Not a production healthcare system
- Not a deployed ML prediction pipeline

## Recommended demo queries

Use these in order:

~~~text
air fryer
Advil
tylonal
NDC 66715 6547
blood sugar monitor
2020 Toyota Camry
~~~

Recommended first two:

- `air fryer` — shows a consumer product / recall-style workflow
- `Advil` or `tylonal` — shows query understanding, drug reference records, and recall-versus-reference distinction

## 60–90 second demo script

> Dav AI is a full-stack public safety intelligence platform I built with React, TypeScript, FastAPI, PostgreSQL, and Alembic. The problem is that public safety information is fragmented across agencies like FDA, USDA, CPSC, NHTSA, and NLM, and different sources mean different things.
>
> The main workflow is Public Safety Search. I can search a product like `air fryer`, and Dav AI checks selected official/public sources, normalizes the results, separates recall or enforcement records from reference and signal records, and links back to the official source.
>
> For drug queries like `Advil` or a typo like `tylonal`, the system applies deterministic query understanding. It can expand a known brand to a generic term, preserve the original query, and explain what else it checked. It avoids uncontrolled fuzzy matching because this is safety-sensitive.
>
> A key design choice is that Dav AI does not say a product is safe or unsafe. A no-match result is not a safety guarantee. The app shows what sources were checked, what kind of evidence was found, and what still needs official verification.
>
> Under the hood, the backend uses source adapters, typed response contracts, fail-soft source orchestration, audit metadata, source registry seeding, and migration alignment tests. The project currently has 393 backend tests and 238 frontend tests passing.

## Screenshot checklist

Capture these screenshots for the README or portfolio page:

1. Home page showing Public Safety as the main path
2. Public Safety Search with `air fryer`
3. A recall/enforcement result card with official source link
4. Public Safety Search with `Advil` or `tylonal`
5. Query Understanding expanded/collapsed section
6. Source Roles or Source Coverage section
7. Sources page showing registered public sources
8. Audit History detail showing provenance metadata
9. Mobile or narrow-screen Public Safety page if it looks clean

Do not lead with ProductScan, Regional Health, System Status, or Saved Monitors.

## Architecture summary

~~~text
React + TypeScript frontend
  -> Public Safety Search UI
  -> FastAPI workflow route
  -> deterministic query understanding
  -> source planning and adapter execution
  -> official/public source adapters and curated official snapshots
  -> normalization, deduplication, ranking, and source-role classification
  -> PostgreSQL audit/source registry/source-pull persistence
  -> typed response contracts and safety-boundary UI
~~~

## Strongest engineering points

- Adapter-based source architecture across heterogeneous official/public datasets
- Deterministic query understanding with typo correction, joined-term cleanup, VIN/NDC/UPC detection, and brand/generic expansion
- Clear separation of recall/enforcement, reference, label, and signal evidence
- Fail-soft behavior with source timeouts and partial results
- Audit and provenance metadata with source IDs, endpoints, timestamps, transform versions, and payload hashes
- Alembic source-registry seed alignment with tests to prevent migration/schema drift
- Typed FastAPI and React contracts
- Outcome-first UI with progressive disclosure
- Responsible safety language and zero-result boundaries
- Automated validation: 393 backend tests, 238 frontend tests, frontend build, ESLint, and Playwright smoke coverage

## Known limitations

- Selected public sources only; not exhaustive
- Some workflows use curated official snapshots for deterministic tests and demos
- Snapshot freshness is not the same as live-source freshness
- No match does not prove safety
- Adverse-event reports do not prove causation
- No complete lot, UPC, NDC package, VIN, UDI, or serial certainty for every query
- No production authentication, tenant isolation, alert delivery, rate limiting, or complete observability
- ProductScan is experimental input assistance only and should not be the main demo
- Offline ML experiments are not production inference

## Interview framing

Use this framing:

> I built Dav AI to solve a real-world data integration and trust problem: public safety records are available, but fragmented and easy to misinterpret. My goal was not to predict safety. My goal was to search selected official sources, classify what kind of evidence was found, preserve provenance, and avoid unsupported claims.

## Resume bullets

- Built a React, TypeScript, FastAPI, and PostgreSQL public-safety intelligence platform that unifies selected FDA/openFDA, USDA FSIS, CPSC, NHTSA, RxNorm, and DailyMed public records.
- Designed source adapters that normalize heterogeneous recall, enforcement, label, reference, vehicle, device, food, drug, and cosmetic records into typed contracts with source-role classification.
- Implemented deterministic query understanding with typo correction, brand/generic expansion, joined-term cleanup, and VIN/NDC/UPC detection while preserving the original user query.
- Added audit and provenance infrastructure with source IDs, endpoints, retrieval timestamps, transform versions, payload hashes, source registry seeding, and migration alignment tests.
- Validated the project with 393 backend tests, 238 frontend tests, TypeScript production builds, ESLint, and Playwright smoke coverage.

## Final demo checklist

Before recording:

- Run backend and frontend locally
- Use Public Safety Search first
- Use `air fryer` and `Advil` or `tylonal`
- Show one official source link
- Show query understanding
- Briefly show Sources or Audit
- Say clearly: “No match is not a safety guarantee”
- Keep demo under 90 seconds
