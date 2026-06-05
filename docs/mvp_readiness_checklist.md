# DAV AI MVP Readiness Checklist

## Purpose

This checklist defines what must be true before DAV AI is considered MVP-ready for portfolio review, demo use, and interview discussion.

DAV AI is a public-data healthcare and everyday safety intelligence platform. It is not medical advice, diagnosis, treatment guidance, clinical decision support, proof of causality, or an official product-safety verdict.

## Current MVP Scope

### Primary MVP Product Story

DAV AI's primary MVP story is now centered on three clear public-data review modules:

- RecallRadar public drug recall search
- DrugSignal public adverse-event search
- FoodRadar public food/supplement/meat/poultry/egg-product recall and public-health-alert search

These three modules are the main demo path and the clearest portfolio narrative: public recall review, public adverse-event reporting-pattern review, and everyday food/supplement safety review.

### Secondary / Extension Surfaces

The following surfaces are implemented or scaffolded, but should be presented as secondary extensions rather than the main MVP story:

- CosmeticSignal public cosmetic adverse-event search
- Regional Health Pulse MVP scaffold for public regional signal workflow design
- Saved Monitors for repeatable public-data checks
- Manual saved-monitor run history
- Latest and previous result comparison
- Payload-change status for saved-monitor runs
- Source freshness scoring
- Source registry transparency
- Audit History with filtering, CSV export, URL deep-linking, and trace copy actions
- Source-pull provenance metadata
- Payload hash, source pull ID, and snapshot ID copy actions
- Backend scheduler-lock protection foundation
- Deterministic monitor insights
- Responsible AI and medical-safety boundary messaging
- Backend and frontend automated test coverage
- CI verification for backend tests, frontend tests, lint, and production build

### Not Included Yet

- User authentication
- Role-based access control
- Alert notifications
- Production scheduled Cron activation
- Public scheduling UI
- Notification preferences
- Clinical decision support
- PHI storage
- LLM-generated medical recommendations
- Production ML, RAG, or deep learning
- ProductScan
- OCR/CNN label scanning
- Personal health data workflows
- Live CDC/HHS-backed Regional Health Pulse connectors

## Engineering Readiness

### Backend

- [x] FastAPI routes are organized by product workflow
- [x] openFDA workflows are separated into service layers
- [x] USDA FSIS recall/public-health-alert workflow is separated into a service layer for FoodRadar
- [x] Audit events are persisted with source, query, timestamp, status, and record count
- [x] Source registry exposes public-data metadata
- [x] Source freshness is deterministic and test-covered
- [x] Saved monitors support manual run history
- [x] Saved-monitor runs include payload-change status
- [x] Source-pull provenance metadata is exposed without raw payload display
- [x] Scheduler-lock protection exists as backend foundation
- [x] Backend test suite passes

### Frontend

- [x] Primary UI story promotes RecallRadar, DrugSignal, and FoodRadar as the main MVP modules
- [x] CosmeticSignal and Regional Health Pulse remain available as secondary/extension surfaces
- [x] Saved Monitors, Data Sources, System Status, and Audit History pages are available
- [x] Saved Monitors display latest/previous values, run history, monitor insights, and payload-change status
- [x] Data Sources and System Status display source freshness signals
- [x] Audit History supports filters, CSV export, deep links, trace copy, and provenance copy actions
- [x] UI avoids presenting public-data signals as medical certainty
- [x] Frontend tests pass
- [x] Lint passes
- [x] Production build passes

### Documentation

- [x] Demo script exists
- [x] Source freshness and payload-change milestone documented
- [x] Production ML roadmap documented
- [x] Responsible AI limitations are stated
- [x] Public-data-only boundary is stated
- [ ] Final portfolio case study should be prepared before sharing broadly
- [ ] Final architecture diagram should be added before interview use

## Verification Commands

Run these before declaring the MVP stable:

bash cd /Users/chanduesukula/dav-ai  source /Users/chanduesukula/dav-ai/.venv/bin/activate  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend -p no:cacheprovider  cd frontend npm test npm run lint npm run build 

## Latest Verification Evidence

Latest confirmed verification evidence:

- Backend tests: 263 passed
- Frontend tests: 70 passed
- Frontend UI story cleanup verified: RecallRadar, DrugSignal, and FoodRadar are promoted as primary landing-page modules
- Frontend lint: passed
- Frontend production build: passed
- Deployment smoke should be re-run after current FoodRadar/CosmeticSignal documentation and any hosted app changes before claiming current deployed readiness
- Live smoke tests confirmed semantic_preview appears in both /api/v1/recalls/search and /api/v1/drug-events/search.
- Recent credibility/documentation improvements: README/docs current MVP scope cleanup, FoodRadar and CosmeticSignal documentation, expanded source registry language, updated public-data safety boundaries, and current verification results.

This evidence supports portfolio MVP readiness for review and demo discussion. It does not indicate production healthcare readiness or clinical validity.
