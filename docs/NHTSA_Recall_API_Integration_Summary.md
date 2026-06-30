# NHTSA Recall API Integration Summary

**Branch:** `feature/nhtsa-recall-api-integration`  
**Status:** Validated live-public-API integration coverage

## 1. Existing NHTSA Support

Dav AI already includes:

- NHTSA vPIC VIN decoding
- NHTSA vehicle recall lookup through `recallsByVehicle`
- year/make/model query parsing
- normalized vehicle recall records in Public Safety Search
- source status, audit metadata, payload hashes, and official NHTSA links

## 2. What This Branch Added

This branch strengthens validation rather than changing application behavior:

- dedicated adapter tests for vPIC decoding, recall payload extraction, normalization, and live-request parameters
- stronger route tests for year/make/model and VIN-driven searches
- assertions for normalized recall fields, structured API metadata, source audits, stored snapshots, and payload hashes

Relevant tags:

- `nhtsa-recall-adapter-tests-v1`
- `nhtsa-route-coverage-v1`

## 3. How Vehicle Search Works

1. A query such as `2020 Honda Civic` is parsed into model year, make, and model.
2. A 17-character VIN query is sent to NHTSA vPIC to decode the vehicle identity.
3. Dav AI sends the resulting year, make, and model to NHTSA's `recallsByVehicle` API.
4. Returned campaigns are normalized, deduplicated, audited, and shown with NHTSA provenance.

## 4. Fields Preserved

NHTSA recall records retain:

- campaign number
- component/hazard context
- summary and consequence context
- remedy
- report-received date
- source provenance, including source ID/name, endpoint, retrieval time, payload hash, and official recall link

## 5. Validation

- **Backend:** 425 passed
- **Frontend:** 250 passed
- **Frontend build:** passed
- **`git diff --check`:** passed

## 6. Limitations

- VIN-specific exact campaign matching remains basic; vPIC identifies the vehicle before a make/model/year recall lookup.
- There is no dedicated Vehicle Recall Check page yet.
- Tires, car seats, and vehicle-equipment recall UX can be expanded later.
- Users should verify VIN-specific recall status through the official NHTSA or manufacturer recall portal.

## 7. Recommended Next Step

Create a small Vehicle Recall Check UI, or enhance vehicle-record source details with clearer VIN-derived identity, campaign, and official-verification context.
