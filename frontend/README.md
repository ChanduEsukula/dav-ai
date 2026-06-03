# DAV AI Frontend

This is the React + TypeScript + Vite frontend for DAV AI.

DAV AI is a healthcare and everyday safety intelligence product prototype that turns public openFDA, USDA FSIS, and scaffolded public-health signal data into source-aware, auditable safety signals and role-based safety briefings.

## Current MVP Status and Limitations

DAV AI is a public-data healthcare and everyday safety intelligence MVP/prototype. It does not provide medical advice, does not use PHI, and does not make diagnosis, treatment, clinical decision-support, patient-risk, safe/unsafe verdict, or causation claims.

The current frontend presents deterministic/rule-based intelligence from backend APIs and frontend utilities. Offline ML experiments exist in the repository, but production ML is not deployed in the user-facing frontend yet. Auth/RBAC, automated alerts, production scheduler activation, notification preferences, and full live Health Pulse data integration remain future work.

The current frontend supports:

- RecallRadar
- DrugSignal
- FoodRadar
- CosmeticSignal
- Regional Health Pulse MVP scaffold
- Safety Briefing Engine v1
- Data Sources page
- Audit History page
- System Status / Data Quality page
- Saved Monitors v2.6 foundation
- Request ID propagation through the shared Axios client
- About / FAQ / support pages
- Frontend tests with Vitest and React Testing Library

---

## Frontend Stack

- React
- TypeScript
- Vite
- Axios
- Vitest
- React Testing Library
- CSS organized by component/page

---

## Current Frontend Features

### Landing Page

The landing page explains the DAV AI product idea, public-data safety intelligence focus, and current MVP modules.

### RecallRadar

RecallRadar allows users to search public openFDA Drug Enforcement recall records and view:

- Matched recall records
- Product descriptions
- Recall reasons
- FDA classification
- Recall status
- Recall initiation date
- Recalling firm
- Distribution pattern
- Transparent Recall Review Score
- Source metadata
- Audit details
- Medical safety disclaimer
- Role-based safety briefing

### DrugSignal

DrugSignal allows users to search public openFDA Drug Event / FAERS records and view:

- Top reported reaction terms
- Relative reaction-count bars
- Record count
- DrugSignal Intelligence Score v1
- Signal strength, review priority, data confidence, and top reaction concentration
- Reaction Classification v1
- DrugSignal Trend Snapshot v1
- Source metadata
- Audit details
- FAERS causation disclaimer
- Medical safety disclaimer
- Role-based safety briefing

Important: FAERS adverse-event reports are reporting patterns only. They do not prove that a drug caused a reaction.

### FoodRadar

FoodRadar allows users to search public food, supplement, packaged grocery, meat, poultry, and egg-product safety records and view:

- Source-checked cards from openFDA Food Enforcement and USDA FSIS Recall API data
- Product descriptions, recall/public-health-alert reasons, status, dates, firms, distribution context, quantity, and code/lot details when available
- Deterministic review-priority scoring
- Highest-score and latest-recall sorting
- Source metadata, retrieval timestamp, and audit context
- Public-data limitations and official-source verification language
- Empty-result handling

Important: a missing FoodRadar result does not prove that a product is safe or unsafe. Users must verify exact product names, lot numbers, establishment numbers, package sizes, and official FDA/USDA source records.

### CosmeticSignal

CosmeticSignal allows users to search public openFDA Cosmetic Event reports and view:

- Cosmetic reporting signal score
- Top reported cosmetic reactions
- Normalized cosmetic-event records
- Source name, endpoint, retrieval timestamp, and audit context
- Query expansion for common terms such as rash, hair dye, mascara, cream, skin, shampoo, fragrance, and deodorant
- Cosmetic adverse-event limitations and public-data boundaries

Important: cosmetic adverse-event reports do not prove causation. Reports may be incomplete, duplicated, delayed, influenced by reporting behavior, or missing context.

### Regional Health Pulse

Regional Health Pulse is implemented as an MVP scaffold for public-health signal review.

Current Regional Health Pulse UI support includes:

- Region and signal-category controls
- Deterministic signal/trend labeling
- Metric cards
- Source metadata
- Audit summary metadata
- Source freshness copy
- Public-health safety boundaries
- Saved Monitors support

Important: Regional Health Pulse is not live CDC/HHS surveillance yet. It is not emergency guidance, not medical advice, and not a personal disease-risk predictor.

### Safety Briefing Engine v1

The frontend includes a deterministic Safety Briefing Engine v1.

It generates role-based briefings for:

- Consumer
- Pharmacy
- Clinic
- Public Health / Analyst

Briefings are generated from structured RecallRadar and DrugSignal response data only. They do not use an LLM yet.

Each briefing includes:

- Summary
- What was found
- What to verify
- Suggested review checklist
- Limitations
- Source and audit details
- Disclaimer

The briefing engine must not provide diagnosis, treatment guidance, medication-change advice, or FAERS causation claims.

### Data Sources Page

The Data Sources page displays registered public/scaffold data sources from the backend source registry endpoint.

Current source categories include:

- openFDA Drug Enforcement API
- openFDA Drug Event API
- openFDA Food Enforcement API
- USDA FSIS Recall API
- openFDA Cosmetic Event API
- Regional Health Pulse MVP scaffold

### Audit History

The Audit History page displays recent persisted public-data audit events when backend audit persistence is configured.

Current Audit History UI support includes:

- Recent audit event table
- Selected audit detail panel
- Module/status/search filters, including Regional Health Pulse
- Applied filter summary
- CSV export
- Copy audit ID
- Copy trace summary
- Copy audit link
- Audit detail URL state
- Source-pull provenance summary when available

Audit History is for public-data traceability only. It is not clinical record storage.

### System Status / Data Quality

The System Status page provides operational transparency into the backend and audit persistence state.

Current System Status / Data Quality UI support includes:

- Backend API status
- Database configured status
- Audit readable status
- Registered source count
- Recent audit count
- Upstream status counts
- Latest audit event summary when available

This is operational transparency, not a full production observability dashboard with alerts, SLOs, or metrics dashboards.

### Saved Monitors

The Saved Monitors page is a v2.6 foundation for repeatable public-data searches.

Current Saved Monitors UI support includes:

- Create repeatable RecallRadar, DrugSignal, or Regional Health Pulse monitor definitions
- List saved monitors
- Delete saved monitors
- Manually run a monitor check
- Show latest score, previous score, record count, last checked timestamp, and latest audit link when available
- Show saved monitor run history
- Show deterministic monitor insights and change indicators
- Preserve internal query spacing while trimming leading/trailing input spaces

Saved Monitors includes backend scheduled-refresh groundwork, CLI guardrails, database-backed scheduler locks, and run-history persistence. Production Cron, public scheduling UI, alert delivery, authentication/RBAC, notification preferences, and briefing history are not implemented yet.

### Request ID Propagation

The shared Axios API client attaches an `X-Request-ID` header to outgoing backend requests. This helps connect frontend actions with backend request logs and response headers during debugging.

---

## Backend Requirement

The frontend expects the FastAPI backend to run locally at:

```text
http://127.0.0.1:8000
