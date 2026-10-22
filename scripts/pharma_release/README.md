# Pharmaceutical release v1 — Phase 1 foundation

Normative specification: [release contract](../../docs/pharma_release_v1_contract.md). This package is offline-only and has no production application imports. Phase 1 creates a schema in memory, registers provenance descriptors there, validates pinned inputs and writes new evidence. It does **not** produce a SQLite pharmaceutical release or ingest identities/evidence.

## Run

From repository root, using existing dependencies:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.pharma_release.build \
  --phase 1 \
  --evidence-dir docs/evidence/pharma-release-v1-build-2026-10-06-phase1-rerun

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  backend/tests/pharma_release/test_phase1.py
```

The evidence directory MUST be new; reruns need a different suffix. Missing/changing inputs and schema/fixture mismatches fail before evidence is created. The CLI only accepts Phase 1. There is no full-build or deployment option yet.

## Current modules

- `schema.py`: executable DDL for exactly 19 STRICT tables; PKs, FKs, enums, indexes and structural evidence guards.
- `ids.py`: lossless namespace-qualified identity codec; existing ingredient/formulation IDs preserved; numeric identity coercion rejected.
- `sources.py`: pinned local source discovery, read-only DuckDB context, input tracking, small-file hash verification, and explicit provenance descriptors.
- `validation.py`: schema/table/PK/FK/integrity validation. It does not certify clinical applicability, ingestion reconciliation, or final publication.
- `build.py`: Phase 1 orchestration using in-memory SQLite, with exclusive creation of evidence outputs.
- `__init__.py`: contract/policy/schema/build versions only.

Future phases should add domain modules only as implemented: identities/eligibility; labels; label applicability/version selection; recalls/applicability; AE; communications/coverage; final manifest/packaging. Existing source assets, contract/evidence, production modules and migrations are not edit targets.

## Physical representation decisions

The executable DDL is authoritative for this implementation and is exported in Phase 1 evidence. These are implementation details within contract v1, not policy amendments:

- IDs use STRICT `ANY` columns with string/nonblank CHECKs. SQLite TEXT affinity otherwise coerces numeric IDs before a type CHECK. No name/NDC/RxCUI product merge occurs.
- Ingredient membership and product identifiers are relational. Formulation ingredient arrays are explicitly permitted source structure; JSON validation triggers additionally enforce referenced ingredients and set uniqueness. Do not project products with unknown full sets onto partial known membership.
- Search and coverage keep their contract composite keys while using nullable typed FK target columns and CHECKs to ensure exactly one correct entity target. No twentieth entity registry table is added.
- Original search-name variants sharing a normalized key are preserved as an ordered source-name array. Evidence identity arrays, verification bases, raw section values, provenance inputs and manifest structures retain JSON where they preserve source structure or documented audit metadata.
- Label/recall edges separate class, identifier method, combination/full-set checks, verification basis, conflicts and consumer eligibility. Candidate classes cannot be consumer evidence. SQL flags are structural guards, not independent proof; later evaluators/validators must substantiate them against sources.
- Labels have per-document dates and per-product selection state. A document is not selected ingredient-wide. SQL also protects selected consumer edges against subsequently invalidating the label document.
- Section values keep full original source text and separate warnings/cautions slots. Missing sections have nullable text and explicit state; schema presence alone does not claim text was extracted.
- AE month keys/window/count semantics are fixed to the contract. Observed-only positive activity is distinct from missing data. Top-rank bounds are enforced; deterministic ranking/reconciliation is Phase 6 work.
- Manifest tables remain empty until Phase 8. External final SQLite SHA256 is supported without putting that checksum inside the SQLite file itself.

All FKs use RESTRICT; no cascade silently removes evidence. The initializer refuses an existing table-bearing database and enables `foreign_keys=ON`. JSON1 and SQLite 3.37+ are required and already available locally. The connection is not exposed through any production route.

## Source/provenance integrity

Phase 1 hashes contract/Step 1 files, small manifests/receipts, raw NDC/enforcement Parquets, identity assets, config and the reference snapshot. Parquet hashes are checked against recorded receipts where supplied. It checks all source sizes/mtimes before and after discovery. Label ZIPs are inspected only for member layout and receipt URL/byte length; no section scan or ZIP CRC traversal is repeated. Research DuckDB is opened with `read_only=True`, one thread, 512 MB memory and disk spill disabled, for `DESCRIBE monthly` only. The application dump is statted, not restored or scanned.

Recorded archive hashes are marked NOT_REVERIFIED unless bytes were freshly hashed. A later extraction stage must verify its bytes/CRC and reconcile content before publication. Configuration URLs do not stand in for preserved communication body text. Missing article capture dates remain NULL until actual stored rows are inspected in Phase 7.

The current eligibility fixture partitions all 138,259 **input** products. Contractually excluded rows remain offline in a final runtime release; normal plus regulatory products total **116,741**. A build may stage excluded rows for reconciliation but must omit them at packaging. Label extraction must reconcile all 262,887 inputs, then package only retained applicable/context documents; unmatched corpus stays offline. These input/runtime distinctions are not source-loss exemptions: rejection/pruning counts and original source references must be auditable.

## Phase boundary

Phase 1 can be inspected independently through its SQL, JSON reports and focused tests. Phase 2 is safe to start once this foundation is accepted, but has not started. No eligibility reclassification, label extraction, applicability decision, FAERS projection, communication ingestion, final manifest or release file is claimed by Phase 1.
