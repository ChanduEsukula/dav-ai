# Dav AI release-candidate verification

2026-10-21, America/Chicago. **Public deployment: NO-GO.** No commit, push, merge, deployment, original database mutation, or publication approval change occurred.

## Candidate and reproducibility

**VERIFIED:** The source-only candidate contains 254 files and no data directory, private environment files, local virtual environment, node_modules, database, backup, report output or Git history. Two separately generated archives have the same SHA-256:

`062fce4f75251b12a892706b733a98270669ecebda82aac348682702ac1e56de`

Archive: `/private/tmp/davai-release-candidate-final-a.tar.gz`. Extracted verification root: `/private/tmp/davai-release-candidate-final`. `candidate.json` records the archive identity; `verification/candidate-manifest.json` records every source hash. All exported source bytes were independently rechecked against the current workspace. This report and generated verification receipts intentionally sit outside the archive so collecting evidence does not change candidate identity.

**VERIFIED:** Both images built from that clean source root using `docker compose -p davai-release-candidate --progress plain build`. No local datasets or private .env files were available to either build. The backend image imports successfully without psycopg/HTTP clients, returns healthy liveness, and denies unapproved readiness. The frontend image passes `nginx -t`. These were one-shot network-disabled container checks; no service deployment was started. Image identities and full build logs are retained in verification/.

**VERIFIED:** Docker base images are digest-pinned; Python runtime dependencies are version/hash-locked in `backend/requirements-runtime.lock`; npm uses package-lock.json and a fresh `npm ci`. Installation in a fresh Python 3.13 test environment and fresh frontend dependency tree succeeded. The first auxiliary fresh-environment run used Python 3.12; the canonical results below were repeated with Python 3.13 explicitly.

**UNKNOWN:** Bit-for-bit reproducibility of image output/attestation metadata was not asserted. Linux amd64 target acceptance, a remote CI run and offline registry availability were not tested. Builds here target the local Docker engine architecture; a successful cached-layer build is not proof of an air-gapped dependency installation.

**VERIFIED:** The current branch is `chore/stabilize-davai-v3`, HEAD remains `4ca92a94a6c27799c3ead5b0b00a91a3afb6fa03`, and the working tree remains uncommitted with unrelated prior work preserved. The verified recovery branch remains `recovery/pharma-before-simplification-20261021` at `0e4c5112f0075199d98bc0436b0f890b5b3b2a11`; all 580 recorded recovery blobs were rechecked. It preserves pre-simplification work. A separate source snapshot before this hardening was saved under /tmp without changing Git. A clean Git checkout of the final app is **not yet available**, because committing is not authorized; the immutable export provides the tested clean-source candidate.

## Verified application and hardening changes

**VERIFIED:** The application remains FastAPI plus React/TypeScript/Vite with 11 OpenAPI paths: service/liveness/readiness, drug search/identity, compatible safety/section/timeline, shared evidence/coverage, and pharmaceutical PDFs. It does not import auth, accounts, LLMs, monitors or multi-domain public routers. Offline research/ingestion tooling is separate and excluded from runtime packaging. Source counts at hardening entry were independently confirmed as 56 backend app files plus 12 frontend source files. The historical 308-file baseline is documented recovery evidence, not a new reconstruction of the obsolete app in this pass.

**VERIFIED, fixed:** Report trailing-slash redirects and unexpected 500s originally lacked no-store headers; an exact-path body limit could be bypassed by the redirect route. The outer ASGI report boundary now covers redirects/errors, checks size before copying chunks, bounds body-read time, rejects report query fields, delivers the buffered request only once and sets private/no-store/nosniff headers. Report validation no longer reflects entered name/age, and unexpected report failures log a fixed event rather than exception text. PDF output is bounded during buffer writes. CORS methods/headers and request-ID length/characters are constrained. Report fields remain escaped, ephemeral, bounded, and posted in the body; filenames are fixed, with no arbitrary URL or filesystem input.

**VERIFIED, fixed:** SQLite originally opened before checksum verification, leaving a file-replacement window, and concurrent cold misses could redundantly hash the full artifact. Verification now precedes opening, checks exact size and formulations along with the other required tables, compares device/inode/size/timestamps, serializes cold hashing and explicitly closes connections on rejection. Regression tests cover replacement, connection closure and warm/cold hashing. The privileged operator filesystem remains a trust boundary.

**VERIFIED, fixed:** A request-ID test originally assumed the external artifact existed, and historical cohort tests assumed local research files. The header test now supplies synthetic metadata. Missing research inputs are reported as unavailable; they are never counted as passing checks. All original research assertions remain when files are mounted.

**VERIFIED, fixed:** Dependency advisory scans initially matched AnyIO/Starlette and frontend packages. Compatible updates moved AnyIO to 4.14.2, Starlette to 1.3.1, Axios to 1.20.0, Vite to 8.3.5 and Vitest to 4.1.12, with transitive lockfile fixes. Final pip-audit runtime and npm all/runtime audits reported zero known vulnerabilities. These are advisory-match checks, not proof of exploitability before the fix or absence of all security flaws. Upstream sources include [AnyIO advisories](https://github.com/agronholm/anyio/security), [Starlette advisories](https://github.com/Kludex/starlette/security/advisories), and [Axios advisories](https://github.com/axios/axios/security/advisories). Exact audit responses are retained.

**VERIFIED:** Offline artifact verification/selection/rollback rehearsal tooling and deterministic candidate packaging were added. Rehearsal pointer updates are locked, atomic and fsynced; verification failure leaves the old selection intact. No production runtime consumes that pointer or accepts it as publication approval. See ARTIFACT_OPERATIONS.md.

## Actual test results

| Classification | Scope | Observed result |
|---|---|---|
| VERIFIED | Final clean-source backend, Python 3.13; isolated PostgreSQL only for offline ingestion | **466 passed, 6 skipped, 7 deselected**, 9.99 s |
| VERIFIED | Missing research cohort coverage | Six skips explicitly identify absent external cohort files; research data validity is NOT established by this run |
| VERIFIED | Required backend release gate, isolated source plus original artifact read-only | **7 passed, 310 deselected**, 5.20 s; no critical skips |
| VERIFIED | Clean frontend fresh npm ci | Passed, no missing package/configuration failure; npm reported zero known vulnerabilities |
| VERIFIED | TypeScript/Vite production build | Passed; 254.74 kB JS, 4.38 kB CSS; total emitted/copied dist 271,406 bytes |
| VERIFIED | Frontend lint / unit tests | Passed / **6 passed** |
| VERIFIED | Artifact-independent real-browser checks | **3 passed**, 2.3 s; desktop/mobile layout and keyboard dialog behavior with recorded API evidence |
| VERIFIED | Required real search-to-PDF browser check | **1 passed**, 8.3 s; actual sealed release, no skip, outbound HTTP blocker log empty |
| VERIFIED | Both application image builds | Passed from the dataset-free source candidate |
| VERIFIED | Backend image import/liveness/denial and frontend Nginx config | Passed, network disabled |
| VERIFIED | Missing/corrupt required artifact | Required pytest gate exits **4**, rather than green/skipped |
| VERIFIED | Selected release tests missing data even without required flag | Exit **1**, four explicit fixture errors identifying missing required artifact; no skipped tests |
| VERIFIED | Required browser gate with missing artifact | **Failed as required** on readiness 503, with exit 1; no skipped test |
| VERIFIED | Missing-data API behavior | Liveness 200; readiness, search, coverage, evidence and PDF 503; PDF response no-store |
| VERIFIED | Production mode with valid artifact present | Liveness 200; pharmaceutical readiness/data/PDF denied 503 |
| VERIFIED | Python syntax, Compose config, git diff --check | Passed |

The seven deselected release checks in the source-only run are not passing checks. The six research skips are not passing checks. The 466 source-only passes plus seven required release passes cover 473 selected checks across separate scoped runs; do not claim all 479 tests passed in a clean dataset-free checkout. The six real-cohort tests were not run against external research inputs here. Required backend integration was run with the sealed pharmaceutical artifact explicitly supplied by read-only path, not copied into the source candidate.

A Starlette test-client deprecation warning about future httpx2 support remains; it is a warning, not a test failure. Earlier isolation/test failures were investigated and fixed, and negative gate failures are intentional evidence. Verification receipts distinguish positive runs, intentional failures, and unavailable data.

## Critical integration checks cannot succeed by skipping

**VERIFIED:** The backend's `release_artifact` marker separates critical real-data checks from source-only tests. Source CI explicitly selects `-m 'not release_artifact'` and prints that it does not qualify release integration. Selecting the real-data tests with no artifact now fails at the fixture/test, rather than skipping. Mandatory staging validation uses:

```sh
PYTHONPATH=backend python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q
```

The required flag verifies checksum/identity/schema before collection, rejects zero critical tests, and fails the session unless every selected critical check has a passed call report. Unit regressions exercise skipped/empty/completed cases. The real browser suite contains no conditional skip and is invoked separately with `PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release`; absent opt-in, readiness, artifact or catalog data fails. Green source-only CI is explicitly insufficient for staging acceptance.

## External installation and approval

**VERIFIED:** The original artifact remains 4,825,108,480 bytes, user_version 4, release ID `dav-ai-pharma-v1-phase4b-communications-20261006`, SHA-256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. The artifact verifier succeeded after the hardening work. Both original metadata copies still record `publication_validated=false`. Neither metadata nor database content was written. Local connections are read-only/query-only; deployment denial remains intact even when the valid artifact is present.

**VERIFIED requirement:** An operator must provision a separate immutable copy/volume outside source, verify exact bytes/checksum/identity/schema/tables with `scripts/manage_pharma_artifact.py verify`, and set `DAV_AI_PHARMA_RELEASE_DB` to a path readable by the runtime UID. Do not edit or replace the original file. Keep rollback copies and operator-only registry paths. Offline ingestion tests additionally need a disposable PostgreSQL test service; historical research validation additionally needs the cohort JSON/CSV and their recorded provenance inputs. Neither is a production application dependency.

**UNKNOWN:** Actual target-environment disk/memory, mount ownership, cold-start budget, ingress policy and approved publication evidence have not been established. Original read-only artifact access here is not a target-volume installation qualification.

**VERIFIED P0 blocker:** Publication approval remains false. There is no authorized public activation record or approved replacement for the temporary deployed denial guard. Public staging/production operation is therefore **NO-GO**. Do not flip the flag or use local mode to evade the guard on a hosted service.

**INFERRED P1 prerequisites:** Before a later authorized rollout, review release-bound/revocable publication authorization, partial recall and retrospective ingredient-cohort coverage, target-architecture acceptance, ingress-wide rate/body/time limits, proxy trust, TLS/origins/hosts, artifact mounts, private request logging, monitoring and rollback. Current PDF limits are process-local; the packaged backend uses one worker and does not trust forwarded client IPs. Container OS/base-image vulnerability scanning and production load/soak tests remain **UNKNOWN**, not passed.

## Files and Git preparation

Existing files edited during this hardening/candidate pass (26):

- `.dockerignore`
- `.github/workflows/ci.yml`
- `README.md`
- `backend/.env.example`
- `backend/Dockerfile`
- `backend/app/db/pharma/release_connection.py`
- `backend/app/main.py`
- `backend/app/routes/reports.py`
- `backend/app/services/report_limits.py`
- `backend/app/services/report_pdf.py`
- `backend/requirements-offline.txt`
- `backend/requirements.txt`
- `backend/tests/conftest.py`
- `backend/tests/pharma_release/test_consumer_label_admission.py`
- `backend/tests/pharma_release/test_explorer_reports.py`
- `backend/tests/pharma_release/test_phase5a_runtime_ask.py`
- `backend/tests/research/test_dav_ai_100_cohort.py`
- `backend/tests/test_request_logging_middleware.py`
- `docs/architecture/PHARMACEUTICAL_EXPLORER.md`
- `frontend/Dockerfile`
- `frontend/README.md`
- `frontend/e2e/pharma-offline.spec.ts`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/playwright.config.ts`
- `frontend/playwright.pharma.config.ts`

New source includes `backend/requirements-runtime.lock`, `backend/tests/pharma_release/test_hardening.py`, `scripts/manage_pharma_artifact.py`, `scripts/prepare_release_candidate.py`, and docs/hardening material. The earlier simplified implementation and unrelated research work remain uncommitted. No destructive cleanup or Git index rewrite was used. Review the full existing working tree separately from this pass's baseline manifest before any separately authorized staging commit.

## Exact next staging task

**VERIFIED next task, no deployment:** Hand the archive/hash, source manifest and verification receipts to the responsible reviewer. In an isolated staging-validation workspace, unpack this exact candidate, provision a separately transported read-only copy of the sealed artifact, verify it, and run the mandatory seven-check backend gate plus the required real browser journey using the documented loopback verification server. Attach the resulting receipts and a release-bound coverage/publication review request. Keep the deployed denial guard and original false approval receipt unchanged.

A reviewer must separately authorize any source commit and any later publication-authorization implementation/cutover. No commit or deployment is authorized by a passing build or local integration test. Public deployment remains **NO-GO**.
