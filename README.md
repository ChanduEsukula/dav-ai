# MedSignal AI

**Healthcare safety intelligence from public FDA signals.**

MedSignal AI is a full-stack healthcare safety intelligence prototype that turns public recall data into source-aware, explainable safety signals. The current MVP focuses on **RecallRadar**, a live FDA recall search workflow powered by the openFDA Drug Enforcement API.

This project is designed as a serious full-stack AI/data product prototype, not a static student demo.

---

## Current MVP: RecallRadar

RecallRadar allows a user to search a product, drug, brand, or category and receive:

- Live public FDA recall records
- Normalized recall details
- Recall reason and FDA classification
- Recall status and initiation date
- Distribution pattern and recalling firm
- Transparent Recall Review Score
- Plain-English explanation
- Source timestamp and technical audit details
- Medical safety disclaimer

The current MVP focuses only on recall intelligence. DrugSignal, Briefing Engine, saved monitors, database persistence, and deployment are planned future phases.

---

## Current MVP Status

### Working now

- React + TypeScript frontend
- FastAPI backend
- openFDA Drug Enforcement API integration
- RecallRadar search workflow
- Rule-based Recall Review Score
- Source-aware audit panel
- Medical safety disclaimers
- Empty-result handling for searches with no FDA matches
- Backend unit tests for recall scoring
- Backend route tests for success, empty-result, and upstream failure cases
- Clean frontend/backend project structure

### Not built yet

- Database or Supabase persistence
- User accounts
- Saved searches or alerts
- Persistent audit logs
- DrugSignal adverse-event module
- AI Briefing Engine
- CI/CD pipeline
- Docker setup
- Production deployment

---

## Current Engineering Status

RecallRadar is the active MVP module. It currently supports:

- Live openFDA Drug Enforcement recall search
- Normalized recall result cards
- Transparent rule-based Recall Review Score
- Source metadata and retrieval timestamps
- Medical safety disclaimer
- Empty-result handling for searches with no FDA matches
- Backend scoring tests
- Backend route tests for success, empty-result, and upstream failure cases

Current backend test status:

```bash
7 passed
```

Recent stability improvements:

- No-match openFDA searches now return `count: 0` and `results: []` instead of a false backend error.
- RecallRadar now displays a clear empty-state message when no FDA recall records match.
- Recall scoring now uses timezone-aware UTC dates.

---

## Recall Review Score

MedSignal AI uses a transparent, rule-based **Recall Review Score** for the RecallRadar MVP.

The score is not a medical diagnosis, treatment recommendation, or official FDA replacement. It is a review-priority signal that helps users understand which public recall records may deserve closer attention.

### Current score inputs

The current score uses four public recall fields:

1. **FDA classification severity**
2. **Recall status**
3. **Recall initiation recency**
4. **Distribution scope**

### Component logic

| Component | Current logic |
|---|---|
| FDA classification | Class I receives the highest weight, followed by Class II and Class III |
| Recall status | Ongoing recalls receive more weight than completed or terminated recalls |
| Recency | Recent recalls receive more weight than older recalls |
| Distribution scope | Nationwide or multi-state distribution receives more weight than local distribution |

The backend returns both the final score and the component-level scores so the result is explainable.

Current score version:

```text
recall-risk-v0.1
```

---

## Safety Boundary

MedSignal AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.

The app does not:

- Diagnose medical conditions
- Recommend medication changes
- Replace FDA, CDC, clinician, pharmacist, or emergency guidance
- Claim that public safety reports prove causation

Users should verify source records and consult qualified healthcare professionals for medical decisions.

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- CSS modules/files
- Axios

### Backend

- FastAPI
- Uvicorn
- httpx
- Pydantic
- pytest

### Public Data Source

- openFDA Drug Enforcement API

---

## Local Development

### Backend

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## Testing

Run backend tests:

```bash
cd backend
pytest
```

Current backend test coverage includes:

- Recall Review Score behavior
- Successful RecallRadar route response
- Empty-result RecallRadar route response
- Upstream failure handling

Run frontend production build:

```bash
cd frontend
npm run build
```

---

## Planned Next Phases

1. Move frontend API base URL into environment configuration
2. Add stronger backend schemas under `backend/app/schemas`
3. Add richer loading and error states
4. Add a source registry and persistent audit trail
5. Add Supabase/PostgreSQL persistence
6. Build DrugSignal adverse-event exploration
7. Build role-specific Safety Briefing Engine
8. Add CI/CD and deployment
9. Add Docker setup
10. Add optional NLP, RAG, and OCR/CNN experiments later

---

## Project Direction

MedSignal AI should remain focused on healthcare safety intelligence, public-data signal monitoring, source transparency, and role-based decision support.

It should not become a generic weather app, generic chatbot, or broad unfocused dashboard.