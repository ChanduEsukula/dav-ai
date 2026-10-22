# Phase 3A — product-scoped FDA label evidence

Build forward from the pinned immutable Phase 2 file. Only `labels`, `label_sections`, `product_labels`, label-domain coverage, label provenance and checkpoint manifest metadata are populated/updated. All changes happen in a **new child directory**. There is no production application integration or PostgreSQL dependency.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.pharma_release.phase3_labels \
  --database data/releases/dav_ai_pharma_v1/phase3-labels-2026-10-06-rerun/pharma.sqlite \
  --evidence-dir docs/evidence/pharma-release-v1-build-2026-10-06-phase3-labels-rerun

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  backend/tests/pharma_release/test_phase1.py \
  backend/tests/pharma_release/test_phase2.py \
  backend/tests/pharma_release/test_phase3_labels.py
```

Both output directories must be new. Failure leaves an explicitly named staging file, never a sealed release. Reruns produce a new versioned directory; they do not overwrite existing releases. The build performs a **real full-corpus replay** in the child before sealing: existing rows must match all original projected fields; no new label/section/edge is inserted. Selection fields are compared through separate semantic guards rather than reset during replay.

The [contract](../../docs/pharma_release_v1_contract.md) and Phase 2 schema are unchanged: 19 tables, no new columns or DDL. The source-qualified label key is the existing lossless codec; `source_record_id`, `set_id`, raw version and effective time remain exact source values.

Modules:

- `label_sources.py`: targeted discovery of the pinned parent and 14 ZIPs/receipts/manifest. Fresh parent/ZIP SHA-256 must match pinned evidence. Only one JSON member is streamed at a time, through EOF for CRC validation; no extraction or network calls.
- `label_extract.py`: six independent structured slots, exact ordered source arrays/strings, full rendering with `\n\n`, separate source/render hashes, exact calendar date/version parsing. `warnings_and_precautions` is preserved only if actually supplied; no absent synthetic seventh slot.
- `label_applicability.py`: every product NDC must have exactly one Phase 2 row with `is_unique_product=1` and `has_conflict=0`. Any missing/ambiguous/conflict-marked NDC rejects the **whole label**. Multi-product labels remain many-to-many; no RxCUI/name/package-NDC override or ingredient fallback.
- `label_build.py`: streaming corpus accounting/admission audit, checked idempotent inserts, per-product/per-source-set version selection, and label-domain coverage.
- `label_validation.py`: strict manual benchmarks, source text/identity projection fingerprints, unchanged parent identity fingerprints, selection/scope/FK/text gates, and field-presence versus usable-text coverage.
- `phase3_labels.py`: fresh copy forward, extraction, semantic validation, complete replay, parent/ZIP preservation rechecks, exclusive final linking and mode `0444`, external final checksum, spot checks and metadata reports.

Two validation dimensions must remain separate:

1. **Strict NDC source linkage:** the user-supplied Phase 3A rule is narrower than contract section 7.5's permission to keep independent edges when another NDC fails. This phase intentionally rejects the whole document if *any* referenced product NDC fails. The rule is versioned in edge verification basis and manifest metadata; contract/policy files are untouched. Clean label/edge/coverage benchmarks refer to this exact linkage rule.
2. **Consumer eligibility:** the existing contract and schema additionally require usable extracted text, valid effective date at/before the export, numeric version, full ingredient and material formulation/scope checks, no contradictions, and per-product/set version selection. Regulatory-only products and uncertain edges cannot become consumer evidence. Unique NDC admission is not a fabricated assertion that unknown kit ingredients were resolved.

Ingredient corroboration uses exact case/whitespace-normalized `substance_name` equality against the **whole preserved product set**, without chemical/salt inference. Route constraints are cross-checked exactly. Supplied product type and RxCUI associations cannot contradict the source product. A complete preserved formulation is required for the consumer scope flag; the explicit NDC enumerates the product formulation/strength. No free-text strength/form parser, clinical-equivalence inference, or summary is introduced. Missing corroboration is recorded, not asserted to agree. Contradictions remain ambiguous regulatory edges even when NDC admission passes.

Versions are selected only within product + source `set_id`. Different sets remain independent. Higher invalid/future/unusable/rejected scoped records make an older viable label explicitly `EARLIER_STORED`; ties with conflicting content or inconsistent version/date order remain ambiguous. No lower year cutoff exists. The full source corpus accounts for rejected candidates and proves no-NDC records have unique, disjoint sets in this capture.

Source numeric versions larger than SQLite's signed integer range are preserved exactly in `version_raw_json`, with `version_number=NULL`, explicit range-unrepresentable audit metadata and no consumer selection. This uses the existing nullable schema rather than clamping, coercing or changing the source version. Source numeric validity and SQLite representability are measured separately.

All admitted labels store six section slots, so absent/blank fields are directly inspectable. Field presence matches the user's manual counts; nonblank usable text matches the earlier Step 1 audit. An inspected missing/blank slot is text capability `UNAVAILABLE`, with a precise reason and NULL/unchanged blank source text. It never means no warning/contraindication/adverse reaction/interaction exists. Invalid shapes are retained and flagged rather than silently coerced or partially dropped.

Clean-label percentages are **source-linkage coverage**, not whole-product safety completeness. Product label-domain states describe the selected scoped payload and known limitations. Identity coverage from Phase 2 is unchanged. Recalls, AE and communications remain empty/unassessed; their manifest unresolved counts remain NULL. The release is a Phase 3A checkpoint, not a deployment/publication certificate.

Parent lineage, archive hashes, capture/export/build dates, exact source identities and strict rule version are recorded. SHA-256 lives outside the SQLite file to avoid self-reference. The original parent and raw FDA archives/receipts are never written.
