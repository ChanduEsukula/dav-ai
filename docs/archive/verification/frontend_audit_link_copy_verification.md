# Frontend Audit Link Copy Verification

Date verified: 2026-05-08  
Feature: Copy audit link  
Frontend: $DAV_AI_FRONTEND_URL

## Summary

The production Audit History page was verified after adding a Copy audit link action to the selected audit event detail card.

Users can now copy a shareable URL for a selected audit event.

## Production verification

Selected audit event:

- Audit ID: 09bb9400-1bce-498d-b9d9-fbdb1b8cafa8
- Module: RecallRadar
- Query: eye drops
- Source: openFDA Drug Enforcement API
- Status: success
- Records: 1

Verified link format:

$DAV_AI_FRONTEND_URL/?page=audit&audit_id=09bb9400-1bce-498d-b9d9-fbdb1b8cafa8

## Verified behavior

- Copy audit link button is visible in the selected audit event card.
- Clicking Copy audit link copies a URL with page=audit and audit_id.
- A copied confirmation message appears.
- Opening the copied URL returns to the Audit page.
- The selected audit event is restored when present in the loaded audit results.

## Why this matters

Copy audit link makes audit traces shareable.

Reviewers and operators can send a direct link to a specific audit event instead of manually copying IDs or explaining where to find the record.

## Current status

Copy audit link is live and working in production.
