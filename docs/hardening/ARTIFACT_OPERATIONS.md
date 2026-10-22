# Artifact operations and required staging gates

Public deployment is **NO-GO**. The original receipt records `publication_validated=false`; no code in this change grants public serving. Production/staging/preview modes keep the deployed-environment denial guard. The offline selection registry described below is a rehearsal tool, not a runtime activation bypass.

## External inputs

The source candidate deliberately excludes all local datasets, private environment files, report output and virtual environments. Install a separately transported read-only copy of the exact release in an operator-managed path accessible to the runtime UID:

- bytes: `4825108480`
- SHA-256: `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`
- SQLite user_version: `4`
- release: `dav-ai-pharma-v1-phase4b-communications-20261006`
- contract: `dav-ai-pharma-release-v1`; policy: `1.0.0`

Do not edit, rebuild, overwrite or chmod the original release. A deployment operator must provision a separate copy/volume, sufficient disk/memory, and read permissions; paths and permissions must work inside the container too. Set `DAV_AI_PHARMA_RELEASE_DB` to that separately mounted copy. No PostgreSQL is needed for application serving.

Before any selection, run `PYTHONPATH=backend python scripts/manage_pharma_artifact.py verify --database /operator/path/pharma.sqlite`. This always checks size, SHA-256, schema, manifest and required tables, including formulations. A successful integrity check still prints publication approval false.

Runtime opens use SQLite read-only/query-only mode, validate the schema, explicitly close connections, and compare device/inode/size/mtime/ctime around opening. Cold hashes are serialized and cached by file identity; the full file is not hashed on every request. A corrupt/replaced/incompatible artifact fails closed. This assumes an operator-controlled immutable filesystem; a hostile privileged local writer is outside that trust boundary.

## Replacement and rollback rehearsal

Use `prepare --database /operator/path/pharma.sqlite --registry /operator/path/private-registry` to record an already-verified immutable file. `select --candidate <returned-id> --registry ...` and `rollback --registry ...` reverify before atomically replacing the registry pointer. Records are retained, writes are locked and fsynced, pending files are cleaned, and a pre-replace failure leaves the previous pointer unchanged. Registry files contain artifact paths and integrity evidence, never report names or ages. No database content is written or copied by these commands.

The application does not consume this pointer. These commands cannot activate public serving or change original publication metadata. The operator must retain old immutable files until their rollback window closes. Future runtime pointer consumption requires a separately reviewed authorization/cutover change and atomic evidence reads; do not repoint a live path behind active requests.

## Source-only verification

With Python 3.13 and Node 24:

```sh
python -m pip install --require-hashes -r backend/requirements-runtime.lock
# In a separate test environment:
python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend python -m pytest backend/tests -m 'not release_artifact' -ra
cd frontend
npm ci
npm run build
npm run lint
npm test
npm run test:e2e
```

`npm run test:e2e` runs the three mocked browser checks only. Source-only backend runs explicitly deselect seven release integration checks. Tests requiring the historical research cohort report missing external inputs as skips; those results do not validate the cohort. PostgreSQL offline ingestion tests require an isolated test server with CREATEDB permission via `PHARMA_TEST_DATABASE_URL`; they do not use an application database. Clean-source CI names this scope explicitly.

## Mandatory release-integration gate

After installing the immutable artifact, run:

```sh
PYTHONPATH=backend python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q
```

This hashes/checks the artifact before collection. Missing/corrupt/incompatible data, no selected critical tests, or any skipped/uncompleted selected critical check makes the command fail. All seven critical checks must pass. Selected release integration tests fail on absent data even without the required-mode flag. The default pytest run is explicitly labelled optional and cannot substitute for the required preflight/no-skip gate.

For the real browser journey, start the test-only outbound-blocking server on loopback with `PORT=18000`, `PYTHONPATH=backend`, `DAVAI_ENV=local` and `ALLOWED_ORIGINS=http://127.0.0.1:15173`. This is local verification, not a staging deployment. Then run `PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release` from frontend. The required browser suite contains no skip: absent opt-in, server, artifact/readiness or catalog data fails. Its API and browser must refer to the same local test service. Stop test services after collecting receipts.

## Publication approval remains a separate blocker

A future approval process must identify an accountable reviewer, immutable release/checksum, evidence and coverage review, approval scope, issuance/expiry and revocation, with a protected/signed authorization record separate from integrity verification. A flag in an operator-editable JSON file is not sufficient evidence by itself. Require release-bound authorization before replacing the deployed denial guard, and test missing/expired/revoked/mismatched authorization plus rollback. No such public activation is authorized in this task. Preserve the original false receipt.

Before public operation, also review ingress-wide limits, proxy trust, TLS/host/origin configuration, artifact mount permissions, monitoring, image/OS vulnerabilities and target-architecture acceptance. PDF rate/concurrency limits remain per process; the packaged server uses one worker and does not trust forwarded client IPs. The report boundary limits bodies and read time, strips reflected validation values, catches report failures without logging their exception text, and applies private no-store/nosniff headers to errors and redirects.


The subsequent managed installer and runtime integration are documented in [staging artifact operations](../staging-artifacts/OPERATIONS.md). Its install/activate/rollback-installed commands use activation.json and immutable copied versions; the legacy active.json rehearsal above remains separate. Hosted serving still requires the unchanged authorization gate.
