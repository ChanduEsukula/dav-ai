# Production Observability Verification

Date verified: 2026-05-07  
Commit verified: 67a9c4a Add structured operational logging  
Backend: https://medtrek-ai.onrender.com

## Summary

Production observability was verified after the structured operational logging milestone.

The deployed backend successfully returned request IDs, reused a custom incoming X-Request-ID, completed a live RecallRadar openFDA search, persisted the audit event to Supabase, and returned the newly created event through Audit History.

## Checks performed

### 1. Health endpoint

Command:

curl -i https://medtrek-ai.onrender.com/health

Result:

- HTTP 200
- Response body: {"status":"healthy"}
- Generated X-Request-ID returned

Generated request ID:

131a3d17-5ad1-4b8d-bc1a-bb256bb944fc

### 2. Custom X-Request-ID reuse

Command:

curl -i -H "X-Request-ID: manual-check-001" https://medtrek-ai.onrender.com/health

Result:

- HTTP 200
- Response body: {"status":"healthy"}
- Response reused custom request ID

Custom request ID:

manual-check-001

### 3. RecallRadar live production search

Command:

curl -i --max-time 30 "https://medtrek-ai.onrender.com/api/v1/recalls/search?q=eye%20drops&limit=5"

Result:

- HTTP 200
- Query: eye drops
- Count: 5
- Source: openFDA Drug Enforcement API
- Upstream status: success
- Score version: recall-risk-v0.1
- Request ID returned

RecallRadar request ID:

c0e46d4c-9b7a-4d92-bd3e-16a9ecc9b215

New audit ID created:

4a19cdf4-81be-4b98-989e-db20c1b35e6b

### 4. Audit History production read

Command:

curl -i --max-time 30 "https://medtrek-ai.onrender.com/api/v1/audit-events?limit=5"

Result:

- HTTP 200
- status: ok
- persistence_available: true
- count: 5
- Audit History returned the newly created RecallRadar audit event

Audit History request ID:

2154379a-903e-498a-9d03-a26f66c4d3dc

Verified persisted audit ID:

4a19cdf4-81be-4b98-989e-db20c1b35e6b

## Production path verified

request -> request ID middleware -> RecallRadar route -> openFDA Drug Enforcement API -> normalization/scoring -> audit event creation -> Supabase insert -> Audit History read

## Current status

The production backend is healthy, traceable, and audit-persistent.

## Follow-up recommendation

Next engineering step should be frontend request ID propagation, so browser requests can generate or preserve X-Request-ID values and make frontend-to-backend debugging easier.
