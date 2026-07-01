# DavAI

DavAI is a full-stack public-data safety intelligence platform prototype that routes product, drug, food, vehicle, device, supplement, and personal-care queries across selected public safety sources with source links, provenance, source-mode context, audit trails, and clear verification boundaries.

The project is designed for portfolio and interview review. It demonstrates modern full-stack engineering, source-grounded search orchestration, auditability, source provenance, and bounded assistant explanations without claiming to be production healthcare, legal, regulatory, AI-safety, or predictive safety software.

DavAI does not decide whether a product, drug, food, vehicle, device, or cosmetic is safe or unsafe. It is not medical advice, legal advice, clinical decision support, emergency guidance, or a replacement for official source instructions.

## Who It Is For

- Normal users who want a clearer starting point for checking public safety records.
- Recruiters and hiring managers evaluating full-stack product engineering.
- Senior engineers evaluating source integration, typed APIs, audit trails, and safety boundaries.
- AI/ML interviewers evaluating whether AI-adjacent features are grounded, bounded, and honestly described.

## Problem

Public safety information is fragmented across agency websites, APIs, labels, reference databases, and official public records. The same search term can mean different things depending on context:

- a formal recall or enforcement action
- a drug label or NDC reference record
- a vehicle recall record
- a medical-device identity record
- an adverse-event signal report
- a public FDA, USDA, CPSC, CDC, VAERS, or NHTSA record

DavAI makes those records easier to search, interpret, and verify while preserving source context. The product goal is not to produce a safety verdict. The goal is:

```text
Search public records -> identify evidence lanes -> verify exact source records -> explain results within clear limits
```

## Main Demo Flow

The current portfolio demo is optimized around **Safety Record Search**.

Recommended 5-minute path:

```text
Home
  -> Safety Record Search
  -> Search "air fryer"
  -> Review evidence types found
  -> Open source verification links
  -> Click Explain These Results
  -> Save or review a repeatable Monitor
```

Recommended demo queries:

- `air fryer`
- `Advil`
- `NDC 66715 6547`
- `Toyota Camry`
- `sunscreen`

## Key Features

| Feature | What it does |
|---|---|
| Safety Record Search | Routes a query across selected public safety sources and separates evidence types such as recall, reference, label, outbreak context, and signal records. |
| Evidence type summary | Shows whether recall/enforcement, reference/identity, label, signal, outbreak, advisory, or other public records were found. |
| Source verification links | Keeps official or public source links visible so users can verify the exact record. |
| Query understanding | Normalizes selected terms, detects identifiers such as NDC, UPC, VIN, and UDI, and exposes how the query was interpreted. |
| DrugSignal | Focused drug recall, public adverse-event signal, label, NDC, RxNorm, and DailyMed-oriented workflow where supported. |
| FoodSignal | Focused food, supplement, meat, poultry, egg-product, outbreak-context, and public-health-alert workflow where supported. |
| Personal Care Signals | Focused cosmetic and personal-care adverse-event report workflow with strong non-causation boundaries. |
| Explain These Results | A bounded assistant entry point that answers using only the current visible result context, source metadata, audit ID, scores, and limitations. |
| Monitors | Repeatable public-record checks with manual run history, change context, and audit links. |
| Audit and Sources | Engineering credibility surfaces for provenance, source registry details, source-pull metadata, payload hashes, and system status. |
| ProductScan beta | Experimental label-text input helper. It is not a production OCR safety decision system. |

## Data Sources and Source Modes

DavAI uses a mix of live public APIs, public-page ingestion, curated official-source snapshots, and prototype scaffolds. The UI and docs should keep those modes visible because they affect what users can honestly infer from a result.

Important source-mode language:

- **Live public API** means DavAI queries an official/public API at request time.
- **Live public-page ingestion** means DavAI reads a public source page or table at request time.
- **Curated official-source snapshot** means DavAI searches a local cache created from official/public source records.
- **Fallback snapshot** means a cached official-source record may be used when a live source is unavailable or not yet integrated.
- **Scaffold/experimental** means the workflow exists for portfolio/product direction but should not be presented as production surveillance or safety verification.

| Source family | Current mode | Notes |
|---|---|---|
| openFDA Drug Enforcement | Live public API | Drug recall/enforcement records. |
| openFDA Drug Event | Live public API | FAERS-style public adverse-event reports; not proof of causation or incidence. |
| openFDA Food Enforcement | Live public API | Food and supplement recall/enforcement records. |
| openFDA Cosmetic Event | Live public API | Cosmetic adverse-event reports; not proof of causation. |
| openFDA Drug Label, NDC, Device Enforcement, Device Event, UDI | Source-specific adapters; some flows use live APIs and some use curated official-source snapshots or fallback data | Used for reference, label, device, signal, and identity context depending on query and adapter. |
| RxNorm/RxNav and DailyMed | Public reference APIs | Used for drug-name, RXCUI, label, and reference context. |
| FDA public recall notices and safety communications | Public-page ingestion or curated official context | Used for official FDA page context where structured APIs are limited. |
| USDA FSIS recalls/public health alerts | Live public API in FoodSignal flows; curated official-source snapshot or fallback in some cross-source flows | Used for meat, poultry, and egg-product recall/public-health-alert context. |
| CPSC consumer-product recalls | Curated official-source snapshot in this prototype | Live automated refresh is not enabled yet. Demo CPSC records should not be used in runtime search. |
| NHTSA vPIC and recalls | Live public APIs | Vehicle decoding and recall lookup paths. |
| CDC/VAERS and CDC/FDA foodborne outbreak context | Public-data signal/context adapters; some flows may use curated official-source snapshots | Signal and investigation context only; not causation or safety verdicts. |
| Regional Health Pulse | Backend scaffold / experimental workflow | Not live CDC/HHS surveillance and should remain outside normal consumer routing unless clearly labeled experimental. |

## Safety and Limitation Boundaries

DavAI is intentionally conservative.

DavAI does not:

- provide medical advice, diagnosis, treatment guidance, or medication-change recommendations
- provide legal advice or official regulatory instructions
- determine that a product is safe or unsafe
- prove that a drug, vaccine, cosmetic, device, food, or product caused an event
- guarantee that an empty search means no public safety issue exists
- provide complete lot, UPC, NDC package, UDI, VIN, serial, or model certainty for every query
- use private patient records, PHI, prescription history, insurance data, or user medical history
- provide production alert delivery, production authentication, RBAC, or tenant isolation; current auth is prototype/demo token-based auth
- claim full production RAG, vector database retrieval, or a production ML prediction system

Users must verify exact product names, identifiers, lot codes, dates, model years, manufacturers, recalling firms, and official source records before acting.

## AI, ML, and Deterministic Logic

DavAI is AI-adjacent, but most of the production-connected intelligence is deterministic.

Implemented now:

- deterministic query normalization and routing
- identifier detection for selected NDC, UPC, VIN, and UDI-style queries
- rule-based source planning and evidence-role classification
- deterministic scoring/review-priority signals
- deterministic semantic-similarity previews and static documentation retrieval experiments
- a bounded assistant route that can use a mock provider by default or an optional configured LLM provider, while receiving only structured current-result context
- offline ML experiments under `backend/ml_experiments`

Not implemented as production claims:

- no production clinical AI
- no production neural-network decision model
- no vector database-backed production RAG
- no autonomous web-browsing assistant
- no production OCR safety decision workflow
- no causation, diagnosis, or personal risk model

The right portfolio wording is:

> DavAI includes a context-grounded assistant over current public-record results and source metadata. It is not a full production RAG system or medical advice product.

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React, TypeScript, Vite, Axios, CSS modules by page/component, Vitest, Testing Library, Playwright smoke coverage |
| Backend | FastAPI, Pydantic, httpx, Uvicorn |
| Persistence | PostgreSQL/Supabase-oriented repositories, psycopg, Alembic migrations |
| Data integration | Source registry, source adapters, public APIs, public-page ingestion, curated official-source snapshots |
| Auditability | Audit events, source pulls, source metadata, request IDs, payload hashes, source freshness/status |
| Assistant | `/api/v1/assistant/chat` with prototype guardrails, structured page context, mock default provider, optional OpenAI/Gemini provider configuration |
| Reports | Bounded PDF report generation with source and limitation context |

## Run Locally

### Backend

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. uvicorn app.main:app --reload
```

The backend defaults to `http://127.0.0.1:8000`.

Useful environment variables:

```text
DATABASE_URL=postgresql+psycopg://...
DAVAI_ENV=local
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
AUTH_SECRET_KEY=
ASSISTANT_LLM_ENABLED=false
ASSISTANT_LLM_PROVIDER=openai
ASSISTANT_LLM_MODEL=
ASSISTANT_LLM_API_KEY=
```

Use `DAVAI_ENV=production` and an explicit `AUTH_SECRET_KEY` in deployed
environments. Deployed-mode persistence failures fail closed for provenance,
monitor, scheduler-lock, and user/profile storage instead of silently using
local/demo fallbacks.

The assistant should remain disabled or use the mock provider unless a backend-only provider key is configured.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend defaults to `http://localhost:5173` and uses:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Docker

```bash
docker compose up --build
```

## Run Tests

Run backend tests from the repository root:

```bash
PYTHONPATH=backend python3 -m pytest backend/tests -q
```

Frontend:

```bash
cd frontend
npm run build
npm test -- --run
npm run lint
npm run test:e2e
```

Current full local validation checkpoint:

- Backend tests: 488 passed
- Frontend tests: 31 files, 282 tests passed
- Frontend production build: passed
- Playwright smoke tests: 3 passed

## Current Status

- Current cleanup focus: recruiter-readiness, documentation clarity, source-mode truthfulness, provenance reliability, and safer deployed-mode persistence behavior.

Recent product polish:

- made Safety Record Search the homepage primary action
- simplified navigation around Safety Search and Monitors
- reduced duplicate homepage sections
- renamed the assistant entry point to **Explain These Results**
- improved Public Safety result hierarchy with **Evidence types found** and **Sources checked and verification links**
- changed user-facing saved-search language to **Monitors**
- removed Regional Health Pulse from normal user-facing routing/copy

## Known Limitations

- DavAI is a portfolio prototype, not production healthcare, legal, or regulatory software.
- Some sources are curated official-source snapshots for deterministic demos, tests, or fallback search, not continuously refreshed live integrations.
- Source coverage is selected and incomplete.
- Public sources may be incomplete, delayed, duplicated, unavailable, or difficult to match without exact identifiers.
- Monitors support repeatable/manual checks and backend scheduling foundations, but production alerting is not enabled.
- ProductScan is experimental label-text assistance, not production OCR verification.
- Explain These Results is bounded to current structured context. It is not a production RAG system, not a web-browsing assistant, and not a source of medical or legal advice.
- Empty search results are not safety guarantees. They only mean DavAI did not find a matching record in the selected sources checked for that query.

## Portfolio Docs

- [Docs Index](docs/README.md)
- [Architecture Overview](docs/architecture_overview.md)
- [Portfolio Demo Package](docs/demo/PORTFOLIO_DEMO_PACKAGE.md)
- [Operations Runbook](docs/operations_runbook.md)
