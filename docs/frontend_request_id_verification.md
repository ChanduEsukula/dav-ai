# Frontend Request ID Verification

Date verified: 2026-05-07  
Commit verified: 8e364b7 Add frontend request ID propagation  
Frontend: https://medtrek-ai.vercel.app  
Backend: https://medtrek-ai.onrender.com

## Summary

Frontend request ID propagation was verified in production after adding the shared Axios API client.

The deployed frontend sends an X-Request-ID header on RecallRadar API calls, and the deployed backend returns the same request ID in the response header.

## Verification evidence

RecallRadar search query:

eye drops

Request URL:

/api/v1/recalls/search

Request header:

x-request-id: db180c79-48f6-450e-ba13-1c89f6612857

Response header:

x-request-id: db180c79-48f6-450e-ba13-1c89f6612857

Result:

- RecallRadar search returned 5 records.
- Audit ID was created in the UI.
- Backend response reused the frontend request ID.
- Browser Network tab and backend logs can now be correlated by request ID.

## Production path verified

browser -> shared Axios apiClient -> X-Request-ID request header -> FastAPI request ID middleware -> backend structured logs -> response x-request-id header

## Why this matters

This allows a user-visible frontend request to be traced through backend logs, openFDA source calls, and audit persistence operations using one request ID.

## Current status

Frontend-to-backend request tracing is active for API calls made through the shared API client.
