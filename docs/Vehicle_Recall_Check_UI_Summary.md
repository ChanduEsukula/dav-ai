# Vehicle Recall Check UI Summary

## Branch

`feature/vehicle-recall-check-ui`

## Commit

- `5fbee9f` — Add vehicle recall check helper

## What changed

This branch adds a frontend-only Vehicle Recall Check helper inside the existing Public Safety Search page. It makes the NHTSA vehicle recall workflow easier for users to discover without adding a new backend endpoint.

## User-facing behavior

The Public Safety Search page now includes a Vehicle Recall Check card that explains users can search by:

- Year / make / model
- VIN
- Vehicle-related products such as tires, car seats, and equipment

The helper includes example searches:

- `2018 Toyota Camry`
- `2020 Honda Civic`
- `4T1B11HK5JU000001`

Clicking a vehicle example submits through the existing Public Safety Search workflow.

## Why this matters

The backend already supports NHTSA recall routing through the real-world safety workflow. This UI makes that capability visible to everyday users and reminds them to verify exact VIN and campaign status on the official NHTSA page.

## Validation

- PublicSafetySearchPage tests: 9 passed
- Frontend tests: 252 passed
- Frontend build: passed
- Backend tests: 425 passed
- `git diff --check`: passed

## Limitations

- This is not a dedicated vehicle page yet.
- VIN-specific verification still depends on official NHTSA confirmation.
- Tires, car seats, and equipment can be expanded with more tailored UX later.

## Recommended next step

Add an Identifier Check Panel that helps users verify VIN, model number, NDC, UPC, lot code, expiration date, and UDI across all public safety workflows.
