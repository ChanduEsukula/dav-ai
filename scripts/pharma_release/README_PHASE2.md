# Pharmaceutical release Phase 2

Builds an **identity-only checkpoint**, using the unchanged [v1 contract](../../docs/pharma_release_v1_contract.md) and Phase 1 foundation. It does not extract or populate labels, recalls, AE, communications, or production search routes.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.pharma_release.phase2 \
  --database data/releases/dav_ai_pharma_v1/phase2-2026-10-06-rerun/pharma.sqlite \
  --evidence-dir docs/evidence/pharma-release-v1-build-2026-10-06-phase2-rerun

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  backend/tests/pharma_release/test_phase1.py \
  backend/tests/pharma_release/test_phase2.py \
  backend/tests/research/test_regulatory_applicability.py \
  backend/tests/research/test_database_health_report.py
```

Both output directories must be new. A staged file remains named `identity.building.sqlite` on failure; it is never substituted for a validated release. A successful file is linked exclusively to its final name and set to mode `0444`. Its SHA-256 is recorded externally to avoid a self-referential checksum. Reproducible row hashes are order-independent sorted SHA-256 row hashes; file timestamps and manifest build time make rerun file checksums differ.

New modules:

- `schema_phase2.py`: five additive product fields on a fresh Phase 1 schema: source application number, dosage form, routes, finished flag, and derived presentation classification. Exactly 19 tables remain. Version is `dav-ai-pharma-sqlite-v1.phase2-identity1`; original Phase 1 DDL and artifacts are untouched. `routes_json` preserves raw ordered routes separately from normalized formulation routes. No manufacturer projection is added.
- `eligibility.py`: ordered contract policy and exact calendar date parsing against September 26, 2026. Missing RxCUI is not an exclusion. Missing formulation can be identity `PARTIAL`.
- `identity.py`: full raw/projection identity join, complete ingredient/formulation checks, explicit membership and identifier relations, source-backed aliases, identity coverage, offline source-universe audit, source-derived expected row fingerprints.
- `search.py`: deterministic exact SQLite lookups by source name role and identifier. Returns every candidate in stable product-ID order. No fuzzy or inferred synonym resolution.
- `validation_phase2.py`: source-projection fingerprints, reference counts, coverage/membership gates, structural checks, and distinct ambiguity measurements.
- `phase2.py`: exclusive fresh artifact creation, provenance, identity build, representative lookup evidence, checkpoint manifest, immutable final-file validation, and preservation verification.

All 138,259 raw source products are reconciled in `source_product_audit.jsonl`. Contractually excluded products remain offline; only normal and regulatory-only products enter SQLite. Ingredient/formulation dictionaries preserve all input rows, including those without retained product references. This does not authorize consumer presentation of an offline product.

The derived presentation classification is distinct from the ordered eligibility mode:

- `NORMAL_CONSUMER_HUMAN_PRODUCT`: contract normal-consumer candidates, including eligible vaccine/plasma types.
- `UNRESOLVED_IDENTITY`: allowed human product types without a complete ingredient set. These remain regulatory-only and searchable by source name or exact identifier; identity coverage is `UNKNOWN`, with nullable measured membership count and no formulation.
- `SPECIAL_REGULATORY_CATEGORY_HUMAN_PRODUCT`: remaining allowed human types classified regulatory-only. Source marketing category and all other deficiencies remain visible; this is not an approval classification.
- `REGULATORY_RESEARCH_ONLY`: unsupported/special source product types; excluded bulk/processing types have this classification in offline audit only.

Unresolved identity is orthogonal to regulatory category; a homeopathic unresolved kit retains both its source category and unknown identity. Classification does not replace raw product type/category. A source brand name is never asserted to be an exclusive commercial brand. Source `labeler_name` remains a labeler field.

Identifier uniqueness/conflict flags measure the **entire source universe**, including excluded rows. Runtime ambiguity is separately measured among retained SQLite candidates. RxCUI concept type stays `UNKNOWN`. Search-name ambiguity across ingredient sets counts only resolved complete sets, with unresolved-name associations reported separately.

Only identity-domain coverage is populated. Regulatory evidence tables remain empty, and the checkpoint manifest marks their unresolved counts as NULL/unassessed. Pinned label dates and AE window in the manifest describe future source scope, not populated evidence or completed projections. Provenance descriptors for future evidence feeds are carried forward from Phase 1, without ingestion.

The builder reuses Phase 1 source discovery: fresh hashes for previously verified inputs; large archive/DuckDB/dump inputs remain size/mtime-only with recorded hashes distinguished from fresh verification. No external calls, ingestion-pipeline changes, PostgreSQL connection, or dependency installation are needed.
