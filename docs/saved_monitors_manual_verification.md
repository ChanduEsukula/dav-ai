# Saved Monitors Manual Verification

Date verified: 2026-05-12  
Environment: Local development  
Frontend: http://localhost:5173  
Backend: http://127.0.0.1:8000  

## Purpose

This document records a manual end-to-end verification of the Saved Monitors v2 foundation. The goal is to confirm that a user can create a saved monitor, manually run a check, receive updated result metadata, and navigate from the saved monitor result to the related Audit History detail.

## Prerequisites

- FastAPI backend running on port 8000.
- Vite frontend running on port 5173.
- Backend health endpoint returns healthy.
- Audit persistence is active when a database is configured.
- Saved monitor persistence may reset in local development when the backend uses in-memory fallback.

## Backend Health Check

Verified:

```bash
curl http://127.0.0.1:8000/health
