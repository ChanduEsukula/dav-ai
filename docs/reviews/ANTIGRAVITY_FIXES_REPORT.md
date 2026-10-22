# Antigravity audit defect fixes

2026-10-22 (America/Chicago). Scope: the three requested defects from `ANTIGRAVITY_APPLICATION_AUDIT.md`. No agentic AI, deployment, commit, push, paid service, cloud configuration change or unrelated research modification.

## Reproduction and root causes

1. **Root environment:** `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' --collect-only -q` reproduced nine collection errors, all `ModuleNotFoundError: No module named 'cryptography'`. The dependency was already correctly pinned in `backend/requirements-dev.txt`; the root environment was stale, while `backend/.venv` had been updated separately. Recreating/activating an existing environment does not install new dependencies.
2. **Offline browser CORS:** started the existing verification script with `ALLOWED_ORIGINS` unset, `PORT=18000` and the complete backend environment. The real-release Playwright test passed its direct API checks but timed out clicking the first product at line 13, reproducing the reported failure (timeout shortened to 15 seconds for reproduction only). The browser origin is `http://127.0.0.1:15173`, whereas the normal app default admits only localhost/127.0.0.1 on port 5173. Direct Playwright API requests do not enforce browser CORS.
3. **Repeated source:** a read-only `release_metadata()` query returned two `openfda_ndc_directory` rows. One references the FDA NDC archive and has an export date/URL; the identity-import row has the same observation timestamp but no export date/URL. Rendering database rows as independent dataset entries produced the apparent duplicate/unavailable-link inconsistency. These are distinct stored provenance records, not database rows safe to delete. A new frontend regression failed before the presentation fix.

## Minimal changes

| File/action | Fix |
|---|---|
| Local root `.venv` | Synchronized the complete existing hash-locked development requirements using `--require-hashes --only-binary=:all:`. No dependency pins changed. `pip check` passes and `cryptography==46.0.7` imports successfully. |
| `README.md` | Specify Python 3.13, consistent root environment use, dependency synchronization after changes, lock/hash validation, and exact two-terminal offline browser commands. |
| `scripts/pharma_offline_server.py` | Set the verification-only default CORS origin to `http://127.0.0.1:15173` before app loading. Preserve explicit `ALLOWED_ORIGINS`, including an empty restriction. Retain loopback binding, outbound blocking and deployed-serving denial. This file was already untracked when work began. |
| `backend/tests/test_offline_verification_server.py` | Four regressions exercise subprocess harness setup, default/existing/empty origin policy, loopback listener parameters, unchanged application defaults and staging denial. No audit hook escapes into the pytest process. |
| `frontend/src/components/StoredDrugCatalog.tsx` | Group source display by dataset name, select an existing allowlisted FDA URL for the summary, and retain every original URL and vintage in expandable provenance details. Explicitly distinguish a record with no stored URL. Preserve raw API evidence and the frozen database. Reuse the existing HTTPS/FDA-host/credential/port checks without broadening them. |
| `frontend/src/components/StoredDrugCatalog.test.tsx` | Add grouping, multiple-vintage, missing-URL, input-preservation and unsafe-link regressions. |
| `frontend/e2e/pharma-offline.spec.ts` | Check the exact browser CORS allow-origin and rejection of an unrelated origin before the data journey, giving a useful failure instead of a click timeout. Verify the grouped real NDC source and missing-URL provenance before downloading the PDF. |
| This report | Record reproduction, scope and final verification. |

The source fix changes presentation only: raw API/PDF provenance records remain intact. It does not infer a URL for the identity-import row or pretend that every same-named record has the same vintage. No changes to `app/main.py` or the normal application CORS default were needed.

## Final verification

Backend verification used the repaired root `.venv`, Python 3.13.7. Frontend tools available locally were Node 25.9.0 and npm 11.12.1; documented/CI target remains Node 24. No Node-version change was required for these fixes.

| Command | Result |
|---|---|
| `.venv/bin/python -m pip check` | No broken requirements. |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_offline_verification_server.py -q` | **4 passed**. |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -ra` | **755 passed, 27 skipped, 7 deselected**, one existing warning (10.92 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/security -q` | **246 passed**, no skips (0.48 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -ra` | **7 passed, 370 deselected**, no skips, one existing warning (8.35 s). Required artifact verification passed. |
| `cd frontend && npm run lint` | Passed; no errors/warnings. |
| `cd frontend && npm test` | **8 passed**, two files. |
| `cd frontend && npm run build` | TypeScript and Vite production build passed. |
| `cd frontend && npm run test:e2e` | **3 passed**: desktop/mobile search-to-PDF and keyboard dialog cancellation (2.6 s). |
| `cd frontend && PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release` | **1 passed**, real frozen-release browser search, provenance, PDF and positive/negative CORS checks (9.0 s). Default test timeout retained. |
| `git diff --check` and new-file whitespace checks | Passed. |

All final checks passed. Initial missing-dependency collection errors, the pre-fix browser timeout and the pre-fix frontend regression are reproduction evidence, not final passing results. The first dependency-install attempt hit sandbox DNS restrictions; the same existing hash-locked install succeeded with network access. Loopback servers/Chromium required local execution outside the restricted sandbox. No authorization gate was changed to make tests pass.

## Preservation and remaining problems

The required artifact verifier checked the sealed SHA256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. Before/after comparisons confirmed unchanged database inode, 4,825,108,480-byte size, modification/change timestamps, read-only permissions and release-metadata SHA256. `publication_validated=false` remains intact. The offline server's outbound-attempt log was empty after the real browser run. Both temporary verification backend processes shut down; Playwright's Vite servers exited with their suites.

The 27 skipped tests still need an optional disposable PostgreSQL ingestion fixture; no PostgreSQL server was started. Seven real-artifact tests were deliberately deselected from artifact-independent regression and passed separately as the mandatory gate. The existing Starlette TestClient/httpx deprecation warning and harmless Playwright `NO_COLOR`/`FORCE_COLOR` warnings remain. Local frontend validation used Node 25 rather than rerunning on the documented Node 24 target.

The identity-import record still correctly has no stored URL in the frozen artifact/API; the UI now explains it under one dataset entry. Independent authorization infrastructure and private ingress acceptance remain separate staging blockers. Serving denial, Vercel/Render configuration and publication metadata are unchanged. Successful local tests do not grant deployment authorization. Existing unrelated untracked pharmaceutical/research files were preserved; no wildcard Git staging or cleanup command was used.
