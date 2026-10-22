# Phase 6.2 — trusted state and security hardening report

2026-10-22 (America/Chicago). Branch: `feat/private-staging-authorization`; baseline HEAD remains `04f3eeb`. **Ready for engineering review of isolated code; private staging and public production remain NO-GO.** No commit, push, merge, PR, deployment or cloud change was performed.

## Ranked findings

These are integration risks in the offline baseline, not demonstrated bypasses of the current hosted denial.

1. **High — caller-controlled trust and identity:** a registry, authority string, deployment string and sequence floor supplied by the same caller are not independent authorization. New policy fixes the interface separation but external policy provisioning/attestation remains required.
2. **High — revocation rollback and replay:** baseline verification accepts equal sequences and stores no state. New strict ingestion and atomic store contract reject lower/equal/conflicting records, and ordinary decisions do not refresh validity. Independent persistence and restore protection remain unimplemented.
3. **High — incomplete legacy revocation/key lifecycle:** unsigned snapshots and the oldest combined helper do not establish authenticated key revocation. New signed-state decisions enforce key/approval tombstones and independently provisioned key windows/status; cumulative revocations cannot be silently removed. Keys cannot alias each other or cross roles. Old APIs remain explicitly offline.
4. **High — access control/origin bypass:** the private proxy has no authentication/TLS and no verified direct-origin protection. The internal network and CORS do not meet staging acceptance requirements. No infrastructure change was made.
5. **Medium — malformed input:** bounded shared UTF-8 parsing, duplicate detection, strict signature inputs and timestamp normalization now reject recursion/excessive integers, malformed clocks and UTC overflow consistently.
6. **Medium — TOCTOU:** artifact hashing/opening and offline decisions/data use remain separate operations. The state reread detects observed changes but is not atomic with future data access. Privileged host writers, trusted time, policy refresh and in-flight revocation semantics remain external obligations.

Detailed evidence, trust boundaries and staging acceptance criteria are in [TRUSTED_STATE_DESIGN.md](TRUSTED_STATE_DESIGN.md).

## Files changed and purpose

| File | Purpose |
|---|---|
| `backend/app/security/validation.py` (new) | Shared bounded strict JSON, signature and time validation; central rejection exception re-exported through the existing authorization module. |
| `backend/app/security/staging_authorization.py` | Apply bounds even for direct verification, validate Ed25519 key/signature types, use common parser/time profile. |
| `backend/app/security/trusted_keys.py` | Apply duplicate/constant/error handling during key selection as well as final claim verification. |
| `backend/app/security/signed_revocation.py` | Common strict parsing/time/signature handling and bounded integer sequence; explicitly document stateless floor semantics. |
| `backend/app/security/revocation.py` | Normalize malformed unsigned snapshot/clock inputs to rejection; retain offline-only status. |
| `backend/app/security/trusted_state.py` (new) | Immutable scoped policy, distinct lifecycle keys, cumulative checkpoint, provider protocol, strictly advancing CAS ingestion and signed-state decision primitives. No production provider or serving integration. |
| `backend/tests/security/test_adversarial_parsing.py` (new) | Malformed/adversarial parsing across direct approval, registry approval and revocation entry points; legacy snapshot validation. |
| `backend/tests/security/test_trusted_state.py` (new) | Synthetic-key policy/state tests: replay, concurrency, simulated external rollback detection, missing state, ambiguous commits, revocations, rotation/recovery, scope and hosted-denial preservation. |
| `docs/security-review/TRUSTED_STATE_DESIGN.md` (new) | Audit, architecture, trust contracts, recovery, lifecycle, logging and unresolved acceptance requirements. |
| `docs/security-review/PHASE62_REPORT.md` (new) | Review summary and exact verification results. |

No frontend, dependency, cloud configuration, active serving gate, frozen artifact or publication metadata change was needed. Existing untracked pharmaceutical/research/ingestion files were left in place.

## Architecture decisions and unresolved dependencies

The new policy/store parameters are trusted dependencies, never request or signed-document trust anchors. Signature verification covers exact original bytes using Ed25519. The new API accepts no arbitrary floor or unsigned revocation snapshot. Existing offline APIs are retained for compatibility and never imported by serving code.

A state provider must authenticate state, serialize concurrent updates, persist the complete checkpoint before acknowledging success, and detect rollback using an independent retained high-water witness. Missing state denies rather than bootstrapping. A locally persisted counter is **not independently rollback-resistant**. The in-memory test fake only simulates the contract and a separate witness; it proves no persistence/restart durability. Reusing a store with a fresh consumer tests the API's lack of an implicit floor reset, not a real process/storage restore.

Provisioned lifecycle policy can immediately revoke an authority key. Recovery uses a new independently trusted authority key, a higher sequence and retained cumulative tombstones. Revocation distribution, authority/root ownership, policy authentication/downgrade protection, persistent provider/recovery, trusted UTC/deployment attestation, TLS/authentication/direct-origin enforcement, external audit logging and per-data-access TOCTOU enforcement still require independent infrastructure and review. No substitute service or production secrets were invented.

## Verification

Executed from repository root using existing Python 3.13.7 environment `backend/.venv`, with `cryptography==46.0.7`.

| Command | Final result |
|---|---|
| `backend/.venv/bin/python -m pytest backend/tests/security -q` | **246 passed**, zero failed/skipped (0.27 s). Includes all 60 baseline tests plus 186 added cases. |
| `backend/.venv/bin/python -m pytest backend/tests -m 'not release_artifact' -ra` | **751 passed, 27 skipped, 7 deselected**, zero failed; one pre-existing Starlette TestClient/httpx deprecation warning (8.25 s). |
| `backend/.venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -ra` | **7 passed, 370 deselected**, zero failed/skipped; same deprecation warning (8.01 s). The locally available real frozen artifact passed the required startup integrity check and selected release checks. |
| `git diff --check` plus whitespace check of new files | Passed. |

The 27 backend skips are optional PostgreSQL ingestion checks without `PHARMA_TEST_DATABASE_URL`; no PostgreSQL service was started. The seven artifact checks were deliberately excluded from artifact-independent regression and separately passed as the required gate. The real gate ran before the final isolated key-alias/boundary additions; release/runtime code did not change, and final backend regression includes all final security changes.

Intermediate test results are not hidden: baseline tests after parser refactoring were 60/60; the first expanded run was **101 passed, 2 failed**, both caused by a new rotation test constructing a forbidden zero-length key interval. Correcting the test fixture produced 216/216; final additional alias, lifetime, payload type and rotation/recovery cases produced 246/246. An intermediate backend run was 721 passed, 27 skipped, 7 deselected before those final 30 cases. No final failures remain. The root `.venv` lacked cryptography, so verification used the existing complete backend environment without installing dependencies.

The real artifact is still read-only, 4,825,108,480 bytes, and the required verifier checks SHA256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. Release metadata retains `publication_validated=false`. Hosted startup/connection denial remains unchanged; a new test demonstrates offline decision success still cannot authorize staging, preview or production connections.

## Remaining staging blockers and disposition

Before private staging, independently provision and qualify the authorization root/key policy, revocation distributor, durable externally witnessed state, recovery procedure, trusted deployment/time identity and private authenticated TLS ingress with no direct-origin bypass. Implement externally retained audit events and reviewed enforcement at startup, readiness and each data access, including in-flight revocation. Complete target storage, browser/API, operational, dependency/image and independent security acceptance. Public publication approval remains separate and false.

**Engineering review: ready. Deployment authorization: not granted.** Passing isolated and real-artifact tests does not authorize serving or deployment. Vercel Authentication and Render Maintenance Mode were not changed.
