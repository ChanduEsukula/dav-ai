# Minimum Render activation — read-only academic demonstration

Implemented on `feat/private-staging-authorization`, based on `fa3367c`. No commit, push, deployment, Render/Vercel change, real grant generation or Maintenance Mode change was performed. The operator's independent Render SHA verification is accepted as the completed artifact-verification prerequisite.

## Changed files

- `.dockerignore`: explicitly include only the authorization dependencies and public boundary in the API image.
- `backend/app/security/publication_candidate.py`: extract the existing signature/scope/lifetime checks for reuse; preserve the original offline candidate's witnessed-revocation behavior and false authorization result.
- `backend/app/security/production_authorization.py`: fixed operator-file locations, pinned public-key fingerprint, exact Render service/code/artifact/review bindings and expiring grants.
- `backend/app/db/pharma/release_connection.py`: retain hosted detection, require the signed gate before/after opening, require a read-only regular production artifact, retain pinned SHA/schema/immutable SQL checks, install an interruptible query deadline.
- `backend/app/services/public_evidence.py`: narrow GET allowlist, anonymous global admission/rate limits, bounded queries/responses, generic errors, fresh authorization before releasing buffered output and opaque projection of recovery-path source IDs.
- `backend/app/main.py`: install the public boundary and emit the accepted approval's SHA-256 at startup. Liveness remains distinct from readiness.
- `scripts/sign_public_evidence_approval.py`: offline operator signer using an existing Ed25519 private key; writes new policy/grant files only. Never uploads or activates anything.
- `backend/tests/security/test_production_activation.py`: focused synthetic grant, real read-only connection, API admission/error and real pinned-artifact positive/negative tests.
- `backend/tests/deployment_foundation/test_public_api_context.py`: validate the updated source-only image boundary, still excluding local research/agent/FAISS/Postgres runtime imports.
- `docs/ai/MINIMUM_PUBLIC_EVIDENCE_ACTIVATION.md`: these exact activation/rollback steps.

No dependency, frontend, database bytes, historical release metadata, original offline approval semantics or hosting configuration was changed.

## Tests

- Final focused activation/candidate/source-image tests: **63 passed** (36 activation tests plus the existing candidate/context checks).
- Security, pharmaceutical, deployment and local-research regression run: **982 passed**, including CORS/liveness and strict Docker-directory exclusion regressions.
- Required real-artifact integration: **9/9 passed**, including positive production-mode reads under a synthetic signed test grant.
- Local source-only Docker build: passed.
- Final isolated container test: 512 MiB, no swap, 0.5 CPU, no network, read-only root/artifact; synthetic grant produced readiness/search/overview **200**, nine Xanax matches, PDF/research **403**, query_only enabled. No real Render authorization was created.
- `git diff --check`: passed. The existing Starlette TestClient deprecation warning remains.

The old false artifact metadata remains unchanged, including projected `publication_authorized=false`; it is historical build metadata, not the live signed permission. The independently verified database is still pinned to 4,825,108,480 bytes and SHA-256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`.

## Exact scope and limits

The signed operation list is fixed in `READ_OPERATIONS`: search, product identity, medication overview, product evidence, exact labels, recall records, ingredient adverse-event evidence, coverage and inventory. All are GET operations. PDF POST, aggregate `/safety`, timeline, communications, API documentation and all research/session/model routes are outside this grant and return 403 when a valid grant exists. Without valid activation, business routes/readiness return generic 503. Local development behavior, local PDF and paired research remain unchanged.

Minimum controls: one Uvicorn worker (existing command unchanged); two simultaneous public reads, one simultaneous medication overview; global 60 requests/minute with burst 10 and immediate 429 (no proxy/IP trust needed); search minimum two characters, catalog limit at most 20, offset at most 1000, one value per query field, 1 KiB query-string ceiling, existing 100-product overview bound; ten-second request budget; eight-second SQLite connection query budget enforced by a progress callback; 2 MiB buffered response ceiling; no-store responses; generic errors with exact-origin CORS where configured. Cooperative SQLite interruption bounds running SQL; this is not a hard OS sandbox or an unconditional wall-clock guarantee for arbitrary blocked I/O. Admission is held until the inner operation returns; no timed-out thread is deliberately abandoned.

Source URLs, dates, applicability, counts and warnings remain intact. Only public projected source-ID strings containing recovery/private acquisition paths become deterministic opaque hashes. Stored provenance and the database are untouched.

## Trust and revocation model

This intentionally implements the requested **minimum operator-managed demonstration model**, rather than deploying the earlier external-witness architecture. Its trust root is the operator-controlled Render environment/Secret Files plus an independently verified public-key fingerprint. An environment boolean, a manifest flag, a request header or a signed grant from an unpinned key cannot activate it. The offline signing key never enters Git, Vite or Render.

A valid signature must bind the exact pinned artifact/release, running image's Python-source digest, operator review-bundle digest, exact Render service ID, public production audience, fixed read scope and a lifetime of at most 24 hours. Startup and every connection/request validate it; responses are withheld if approval changes/expires during processing. Preview/staging/conflicting environment markers remain denied.

The earlier offline candidate validator still requires its original independently witnessed revocation state. It has not been silently weakened or turned into a runtime bypass. This new demo gate instead uses expiration and operator revocation through Maintenance Mode plus grant/pin removal and restart. It does **not** claim independently witnessed anti-rollback, continuous external revocation or protection from a compromised Render operator account. An unexpired grant can be restored by that trusted operator; expiry remains enforced. Renewing grants is an explicit operator action, not an automatic self-approval loop.

## Remaining launch blockers

Only the deployment actions below remain for this implementation:

1. Explicit operator approval/signing of the final image and scope; provision its public policy, grant and matching key fingerprint. No real key or grant was created by this task.
2. Ensure the existing Render artifact is a regular non-symlink file with **no write permission bits** and is readable by the non-root API identity. Keep its directory operator-controlled and its SHA unchanged. The gate rejects writable production artifacts. No database/permission change was performed here.
3. Deploy the exact candidate under Maintenance Mode after explicit deployment approval, verify readiness and the limited browser/API flow, then obtain the separate decision to disable Maintenance Mode. This task does not authorize that action.

No new audit program, external state service, Postgres, RAG/model hosting or architecture migration is a prerequisite of this minimum implementation. PDF and hosted research are intentionally unavailable, not unfinished activation features.

## Exact activation steps — operator only, not performed

### 1. Build and fingerprint the final runtime

From the repository root after reviewing/approving the exact code candidate:

```bash
docker build --tag dav-ai-activation:local --file backend/Dockerfile .
docker run --rm --network none --entrypoint python dav-ai-activation:local \
  -m app.security.production_authorization digest
```

Record the resulting 64-character application digest. Use the digest from the **source-only runtime image**, not from `PYTHONPATH=backend` in the full developer checkout. Render must build the same reviewed source-only context; the digest ignores file timestamps and is deterministic over runtime Python source bytes. Do not edit backend source after signing. An image with different Python source fails closed.

### 2. Sign offline, outside the repository

Use an existing operator-owned Ed25519 PEM private key (mode 0600). If a new operator key is needed, create it in a protected directory outside the repository with `umask 077` and `openssl genpkey -algorithm ED25519 -out operator.pem`; never paste its contents into the repository, service environment or dashboard.

Create a short approval record outside the repository documenting the noncommercial academic demonstration, pinned artifact hash, approved read-only scope and intended Render service. This is the review-bundle file below. Then, from the repo root, fill the operator-owned absolute paths and the real Render service ID:

```bash
PYTHONPATH=backend .venv/bin/python scripts/sign_public_evidence_approval.py \
  --private-key /SECURE_OPERATOR_DIRECTORY/operator.pem \
  --review-bundle /SECURE_OPERATOR_DIRECTORY/approval-record.txt \
  --application-sha256 APPLICATION_DIGEST_FROM_STEP_1 \
  --render-service-id ACTUAL_RENDER_SERVICE_ID \
  --approval-id dav-ai-academic-demo-APPROVAL_IDENTIFIER \
  --hours 24 \
  --output /SECURE_OPERATOR_DIRECTORY/NEW_APPROVAL_OUTPUT_DIRECTORY
```

The output directory must not exist. The signer returns the public `signing_key_sha256`, approval payload digest and expiry; preserve these receipts and the signed files privately as the operator's approval evidence. No private-key material is printed or copied into the output. Choose `--hours 1` through `24`; no longer lifetime is accepted.

### 3. Provision only these Render values

Keep Maintenance Mode **on**, Auto-Deploy **off**, the existing persistent disk and `backend/Dockerfile`, one Uvicorn worker and existing port handling. Set the Render health-check path to `/health`; use `/ready` for permission/data readiness checks, not the liveness probe. In the service Environment settings, use **Save only** for environment edits while preparing the controlled activation:

```text
DAVAI_ENV=production
DAV_AI_PHARMA_RELEASE_DB=/data/pharma/pharma.sqlite
DAV_AI_PHARMA_REQUIRE_READY_AT_STARTUP=1
DAV_AI_PUBLIC_KEY_SHA256=<signing_key_sha256 from the operator receipt>
ALLOWED_ORIGINS=<exact HTTPS production/approved Vercel frontend origin>
```

Do not set `DAV_AI_PHARMA_ARTIFACT_ROOT` alongside the explicit file path. Remove conflicting `APP_ENV`, `ENVIRONMENT` or `PYTHON_ENV` values, or set them to production. Do not override Render's automatically supplied `RENDER=true` and `RENDER_SERVICE_ID`; the latter must match the signed service ID. No database URL, pairing capability, Ollama/FAISS setting or signing private key belongs in this public runtime. The existing frontend API base remains `https://medtrek-ai-backend.onrender.com`; no Vercel configuration change is required by this backend implementation.

Add exactly two **Render Secret Files** using the generated public-policy/grant contents:

| Filename | Runtime path |
| --- | --- |
| `dav-ai-public-policy.json` | `/etc/secrets/dav-ai-public-policy.json` |
| `dav-ai-public-approval.json` | `/etc/secrets/dav-ai-public-approval.json` |

Do not upload `operator.pem`. Regular Secret Files and Render's exact `filename -> ..data/filename` layout are supported; `..data` may be a real directory or a relative symlink to one real `..generation` directory immediately inside the canonical Secret Files root. Files and real directories must not be group/world writable. Other symlinks, traversal, nonregular targets and changes during a read deny activation. The cryptographic checks are unchanged; this source change requires rebuilding and signing the new image digest. **Saving Secret Files triggers a Render deployment**, so do this only when the deployment itself has been explicitly approved and Maintenance Mode remains on. If values are saved before the candidate code is available, the previous gate remains closed; do not turn off maintenance to troubleshoot it. Provider references: [Render environment/Secret Files](https://render.com/docs/configure-environment-variables), [automatic service identity](https://render.com/docs/environment-variables).

### 4. Verify under Maintenance Mode

After explicit approval to deploy the candidate and settings, allow the controlled Render deployment. The startup log must include `public_evidence_authorization_verified approval_sha256=...` matching the receipt. Wrong code/service/key/artifact, expired approval or absent files must refuse startup. No override flag fixes an invalid grant.

In the authorized Render shell, check the internal listener while public Maintenance Mode still returns 503:

```bash
curl --fail --silent "http://127.0.0.1:${PORT:-8000}/ready"
curl --fail --silent "http://127.0.0.1:${PORT:-8000}/api/drugs/search?q=Xanax"
curl --fail --silent "http://127.0.0.1:${PORT:-8000}/api/medications/overview?q=Xanax"
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --request POST "http://127.0.0.1:${PORT:-8000}/api/local/research/sessions"
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --request POST "http://127.0.0.1:${PORT:-8000}/api/v1/reports/pharmaceutical"
```

Expected: 200, 200, 200, **403**, **403**. Verify selected-product `/evidence` and `/safety/labels`, recall reasons and ingredient-level warnings. Do not describe PDF or hosted AI as available. A disabled public site remains expected until a separate explicit decision to turn off Maintenance Mode; do not perform that decision as part of this implementation task.

### 5. Renewal and rollback

- Grants expire after at most 24 hours. Renewal: sign a new grant/policy into a new output directory for the **same approved image digest and actual service ID**, using the existing offline key; replace the two Secret Files through an explicitly approved controlled deploy. Keep a receipt for the new approval. If renewal is missed, business reads/readiness fail closed; health is only liveness, and a subsequent restart refuses startup.
- Immediate rollback/revocation: enable/retain Maintenance Mode first. Remove the grant Secret File or the `DAV_AI_PUBLIC_KEY_SHA256` pin and restart/redeploy through the approved operator process. Verify business access/readiness is 503. Secret-file edits are not assumed to hot-reload in Render; Maintenance Mode is the immediate public cutoff.
- Never set Render to local, flip the false artifact metadata, disable the gate or repair the SQLite file to recover service.
- A code rollback changes the application digest. Either remain closed or explicitly reapprove/sign the intended previous image. Old grants cannot authorize different code. An unexpired grant for the identical code/service remains valid under this operator-managed model; do not restore one unintentionally.
- The existing local PDF/research workflows are unchanged and remain private. No hosted pairing/model endpoint is part of activation or rollback.
