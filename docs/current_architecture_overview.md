# DAV AI Current Architecture Overview

Date: June 2026  
Status: Current portfolio MVP architecture summary

DAV AI is a public-data healthcare safety intelligence prototype. It is designed to help reviewers search, score, audit, brief, monitor, and compare public safety signals from trusted public sources.

DAV AI is not production healthcare software. It is not medical advice, not diagnosis, not treatment guidance, not clinical decision support, and not a medical device. It does not use PHI or private patient records.

## Current Product Identity

The active project name is **DAV AI**.

Older planning materials may reference MedSignal AI or MedTrek AI. Those names should be treated as historical proposal or planning context. The current repository and portfolio identity should use DAV AI.

## Implemented Today

- React, TypeScript, and Vite frontend.
- FastAPI backend.
- RecallRadar search using openFDA Drug Enforcement public data.
- DrugSignal search using openFDA Drug Event public data.
- Regional Health Pulse MVP scaffold for public-health signal workflow design.
- Source Registry and Data Sources visibility.
- Audit History for public-data traceability.
- Source-pull provenance records.
- Raw public-source snapshot persistence where supported.
- Stable SHA-256 payload hashing for reproducibility and change review.
- Deterministic Recall Review Score and DrugSignal intelligence outputs.
- Deterministic role-based safety briefings.
- Saved Monitors manual workflow for repeatable public-data searches.
- Saved-monitor manual run history and latest/previous comparison.
- Backend scheduled-refresh foundation and CLI guardrails.
- Database-backed scheduler lock foundation.
- Offline ML experiments under `backend/ml_experiments`.
- Backend and frontend automated test coverage.

## Partial / Scaffold

- Regional Health Pulse is a scaffolded MVP workflow. It is not live CDC/HHS surveillance, not outbreak detection, not emergency guidance, and not personal disease-risk prediction.
- Saved Monitors support manual review and backend scheduling groundwork, but they are not production alerting.
- Scheduler logic and Render Cron planning exist, but production Cron activation is not enabled.
- Offline ML experiments exist for responsible AI/ML framing, but no production ML model is deployed in the API, frontend, scheduler, saved-monitor workflows, or alerts.

## Planned / Future Work

- Authentication and role-based access control.
- User ownership for saved monitors and audit records.
- Production Cron activation.
- Public scheduling UI.
- Notification preferences.
- Automated alert delivery.
- Production scheduler observability.
- Live CDC/HHS-backed Regional Health Pulse connectors.
- Briefing persistence/history.
- Source-grounded RAG or LLM briefing assistant after retrieval, citation, and guardrail evaluation mature.
- Semantic search after source grounding and evaluation are stronger.
- CNN/OCR label scanner as a later optional feature, not a current MVP priority.

## Not Implemented

DAV AI does not currently include:

- Production healthcare operations readiness.
- Clinical decision support.
- Diagnosis, treatment, medication-change, or causality guidance.
- PHI storage.
- Real user accounts or RBAC.
- Production alerting.
- Production ML.
- LLM/RAG assistant.
- CNN/OCR product-label scanning.
- Live outbreak surveillance.

## High-Level Architecture

```mermaid
flowchart LR
    User[Reviewer / Demo User] --> FE[React + TypeScript + Vite Frontend]

    FE --> API[FastAPI Backend /api/v1]

    API --> RR[RecallRadar Workflow]
    API --> DS[DrugSignal Workflow]
    API --> RHP[Regional Health Pulse Scaffold]
    API --> SM[Saved Monitors]
    API --> AH[Audit History]
    API --> SR[Source Registry]

    RR --> OFDA1[openFDA Drug Enforcement API]
    DS --> OFDA2[openFDA Drug Event API]
    RHP --> Scaffold[Scaffold Public-Health Source]

    RR --> Audit[Audit Events]
    DS --> Audit
    RHP --> Audit
    SM --> Audit

    RR --> Pulls[Source Pulls]
    DS --> Pulls
    RHP --> Pulls

    Pulls --> Snapshots[Raw Public-Source Snapshots]
    Snapshots --> Hashes[SHA-256 Payload Hashes]

    Audit --> DB[(PostgreSQL / Supabase)]
    Pulls --> DB
    Snapshots --> DB
    SM --> DB
    SR --> DB

    API --> Briefings[Deterministic Safety Briefings]
    API --> Scores[Deterministic Scores]

    ML[Offline ML Experiments] -. not production .-> Docs[AI/ML Roadmap + Portfolio Story]
