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
- Backend unit tests for recall scoring
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