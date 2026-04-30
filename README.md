# MedSignal AI

**Healthcare safety intelligence from public FDA signals.**

MedSignal AI is a full-stack healthcare safety intelligence prototype that turns public recall data into source-aware, explainable safety signals. The current MVP focuses on **RecallRadar**, a live FDA recall search workflow powered by the openFDA Drug Enforcement API.

This project is designed as a serious full-stack AI/data product prototype, not a static student demo.

## Current MVP: RecallRadar

RecallRadar allows a user to search a product, drug, brand, or category and receive:

- Live public FDA recall records
- Normalized recall details
- Recall reason and FDA classification
- Recall status and initiation date
- Transparent recall risk score
- Plain-English explanation
- Source timestamp and technical audit details
- Medical safety disclaimer

## Architecture

```text
medsignal-ai/
├── backend/
│   └── FastAPI backend
│       ├── openFDA connector
│       ├── RecallRadar route
│       └── transparent recall scoring
│
├── frontend/
│   └── React + TypeScript frontend
│       ├── professional landing UI
│       ├── live RecallRadar search
│       └── source/audit display
│
└── README.md
