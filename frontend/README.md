# MedSignal AI Frontend

This is the React + TypeScript frontend for MedSignal AI.

The current frontend supports the RecallRadar MVP, which allows users to search public FDA recall records, view recall details, inspect Recall Review Scores, and see source-aware audit information.

---

## Frontend Stack

- React
- TypeScript
- Vite
- Axios
- CSS organized by component/page

---

## Current Frontend Features

- MedSignal AI landing page
- RecallRadar search interface
- Recall result cards
- Recall Review Score display
- Audit/source metadata panel
- About page
- FAQ page
- Help/Profile/Sign Up placeholder pages
- Medical safety disclaimer messaging

---

## Backend Requirement

The frontend currently expects the FastAPI backend to run at:

```text
http://127.0.0.1:8000