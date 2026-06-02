# DAV AI MVP Readiness Checklist

## Purpose

This checklist defines what must be true before DAV AI is considered MVP-ready for portfolio review, demo use, and interview discussion.

DAV AI is a public-data healthcare safety intelligence platform. It is not medical advice, diagnosis, treatment guidance, clinical decision support, or proof of causality.

## Current MVP Scope

### Included

- RecallRadar public drug recall search
- DrugSignal public adverse-event search
- Regional Health Pulse public regional signal workflow
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

## Engineering Readiness

### Backend

- [x] FastAPI routes are organized by product workflow
- [x] openFDA workflows are separated into service layers
- [x] Audit events are persisted with source, query, timestamp, status, and record count
- [x] Source registry exposes public-data metadata
- [x] Source freshness is deterministic and test-covered
- [x] Saved monitors support manual run history
- [x] Saved-monitor runs include payload-change status
- [x] Source-pull provenance metadata is exposed without raw payload display
- [x] Scheduler-lock protection exists as backend foundation
- [x] Backend test suite passes

### Frontend

- [x] RecallRadar, DrugSignal, Regional Health Pulse, Saved Monitors, Data Sources, System Status, and Audit History pages are available
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

```bash
cd /Users/chanduesukula/dav-ai

source /Users/chanduesukula/dav-ai/.venv/bin/activate

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend -p no:cacheprovider

cd frontend
npm test
npm run lint
npm run build
```

## Latest Verification Evidence

Latest confirmed verification evidence:

- Backend tests: 205 passed
- Frontend tests: 8 test files passed, 64 tests passed
- Frontend lint: passed
- Frontend production build: passed
- Vercel deployment: Ready after recent merged PRs
- Recent credibility/documentation improvements: README current MVP scope cleanup, current architecture overview added, historical checkpoint docs labeled, backend upstream error responses sanitized, PDF report route coverage added, and source-pull provenance testing strengthened so raw payload contents are not exposed in API responses.

This evidence supports portfolio MVP readiness for review and demo discussion. It does not indicate production healthcare readiness or clinical validity.
