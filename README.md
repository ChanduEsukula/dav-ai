# Dav AI

Dav AI is a read-only FDA pharmaceutical evidence explorer built with FastAPI, React, TypeScript and Vite. Search by brand, generic name, active ingredient or NDC, select an exact stored product, compare product-linked recall history with ingredient-level reported adverse events, and download a personalized PDF evidence report. No accounts, chatbot, LLM, monitoring jobs or external lookup are part of the application.

## Local development

Use Python 3.13 and Node 24. The existing frozen SQLite release is mounted separately and must never be rebuilt or edited during application development.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r backend/requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -c 'import cryptography; print(cryptography.__version__)'
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Use the root `.venv` consistently for these commands. Re-run the locked install after pulling dependency changes, even when `.venv` already exists; recreating or activating an old environment does not synchronize it. `cryptography` is required by the security suite and is already pinned in the development lock file. A separate `backend/.venv` is not automatically synchronized with the root environment.

In another terminal:

```sh
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

The default artifact is `data/releases/dav_ai_pharma_v1/phase4b-communications-2026-10-06/pharma.sqlite`. Override with `DAV_AI_PHARMA_RELEASE_DB` only for a mounted copy of that exact release. Required SHA-256: `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. The read-only connection verifies schema, release identity, policy and checksum; cached integrity checks are invalidated by file metadata changes. Missing/incompatible artifacts return 503, never fall back to PostgreSQL.

`docker compose up --build` is a local-only alternative. Ports bind to loopback and the artifact mounts read-only. The production image defaults to `DAVAI_ENV=production`, which denies pharmaceutical serving. Local Compose explicitly sets `local` for verification.

## Evidence and reporting

The explorer and PDF endpoint consume the same frozen-repository evidence contract. The PDF form requests a required name (1–100 characters) and optional integer age (0–120); title and medication are automatically populated. These fields identify the report only. PDFs are returned directly from memory with `no-store` headers and a fixed download filename. Names and ages are neither persisted nor put in URLs or request logs. Do not add request-body capture at an observability proxy.

The report endpoint bounds request bodies (4096 bytes), generation concurrency (2 per process), per-client generation (5/minute), evidence size (1.5 MB), linked recalls (200), ingredients (20), reaction rankings (50/ingredient), months (78/ingredient), and final PDF size (5 MB). Oversized evidence fails explicitly, rather than silently dropping recall records. Rate limits are process-local and do not trust forwarded client IPs; an eventual multi-worker public release needs an ingress-wide limiter and reviewed timeout/body policies.

An NDC-listed labeler is not independently verified as the manufacturer. A recalling firm is separately attributed from the recall record. Missing linked recalls never establish that no historical recall exists. Adverse-event counts describe ingredient-report associations and co-reported reactions, not incidence, causality, comparative safety, patient counts, or personal risk. Component counts must not be summed into product totals. Name and age do not change the evidence or generate medical recommendations.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service description |
| GET | `/health` | Liveness independent of artifact |
| GET | `/ready` | Artifact integrity and authorization gate |
| GET | `/api/drugs/search` | Bounded consumer-eligible search |
| GET | `/api/drugs/{product_id}` | Exact product identity |
| GET | `/api/drugs/{product_id}/evidence` | Shared explorer/PDF evidence |
| GET | `/api/drugs/{product_id}/safety` | Compatible stored safety contract |
| GET | `/api/drugs/{product_id}/safety/{section}` | Compatible stored section read |
| GET | `/api/drugs/{product_id}/timeline` | Compatible stored timeline |
| GET | `/api/coverage` | Release version, source vintages and limitations |
| POST | `/api/v1/reports/pharmaceutical` | Ephemeral personalized evidence PDF |

Product IDs are opaque and must be URL-encoded. Interactive schema is available at `/docs`; the PDF response contract is included. Compatibility safety/timeline reads retain eligible labels and curated communications; the primary interface displays recalls and adverse events.

## Verification

```sh
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -ra
.venv/bin/python -m compileall -q backend/app scripts/pharma_release
.venv/bin/python scripts/verify_runtime_artifact.py
cd frontend
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Default browser tests use recorded evidence and exercise desktop/mobile layout and the PDF form. For a real frozen-release search-to-PDF browser journey, start the verification server from the repository root:

```sh
PORT=18000 PYTHONPATH=backend .venv/bin/python scripts/pharma_offline_server.py
```

Then run in another terminal:

```sh
cd frontend
PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release
```

The verification server binds only to loopback, blocks outbound FDA/provider HTTP, and defaults CORS to the exact Playwright frontend origin `http://127.0.0.1:15173`. An explicitly set `ALLOWED_ORIGINS` is preserved; if it excludes that origin, the browser test will be blocked. This harness setting does not change the application's default CORS policy or authorize hosted serving. Stop the verification server with Ctrl-C when finished.

Offline PostgreSQL tests require `PHARMA_TEST_DATABASE_URL` pointing to a disposable server with CREATEDB permission. They create/drop uniquely named test databases; never point them at a recovery backup. Selected release integration tests fail when the artifact is absent; explicitly deselect them for source-only checks. CI runs synthetic artifact, policy, PDF, ingestion, research and browser checks without distributing the large local release.

## Offline tools and preservation

`backend/requirements.txt` is the API runtime. `requirements-offline.txt` adds PostgreSQL migration/ingestion and streaming build tools; `requirements-research.txt` adds DuckDB/PyArrow; `requirements-dev.txt` combines test/build requirements. PostgreSQL is an offline tool, not an application requirement. Historical migrations and legacy experiment datasets remain for audit/reproducibility and are not loaded by the public API or copied into its image.

Keep all frozen releases, regulatory archives, raw/research data, PostgreSQL backups, manifests and prior validation receipts untouched. See [current architecture](docs/architecture/PHARMACEUTICAL_EXPLORER.md), [simplification inventory](docs/simplification/INVENTORY.md), and [implementation report](docs/simplification/REPORT.md).

## Publication status

The existing receipt still records `publication_validated=false`. Local integrity verification does not authorize publication. No public deployment, push or merge is part of this cleanup. Antigravity should review the source diff, evidence coverage and publication policy before designing a separately versioned reduced artifact or an explicit activation process.


Release-candidate verification and artifact installation are documented in [artifact operations](docs/hardening/ARTIFACT_OPERATIONS.md). Source-only checks do not validate external data. The mandatory backend release gate is `PYTHONPATH=backend python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q`; it fails on missing data or skipped critical checks. Runtime dependencies are hash-locked in `backend/requirements-runtime.lock`, and both Dockerfiles pin their base images. Public deployment remains NO-GO.


Managed artifact installation, atomic selection, restart pinning and recovery commands are available in [staging artifact operations](docs/staging-artifacts/OPERATIONS.md). The private staging Compose file is a configuration blueprint only: it publishes no ports and retains the staging/production serving denial. No publication approval is implied by installation or activation.
