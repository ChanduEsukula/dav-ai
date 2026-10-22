# Staging artifact installation and recovery report

2026-10-21 (America/Chicago). The prior release-candidate report was read and retained as authoritative context. **Artifact installation/recovery is implemented and validated. Hosted staging serving and public deployment remain NO-GO pending authorization.** No commit, push, merge, cloud provisioning or deployment occurred.

## Installation architecture

**VERIFIED:** `backend/app/db/pharma/artifact_store.py` implements a provider-neutral POSIX persistent store. The offline operator installs independent copies under `releases/<version>/`, with immutable database/receipt files and directories. The API mounts the store read-only. No installer/activation HTTP endpoint was introduced.

Installation streams into a newly created hidden directory, bounds copied size, checks source stability and streamed SHA-256, fsyncs the copy, rehashes and verifies the copied SQLite release, writes a receipt, then publishes the version directory by same-filesystem rename. Existing versions are never overwritten. Checksum, exact size, release ID, contract/policy, schema user_version and all 19 required tables must match before publication or selection. SQLite sidecars are refused and SQLite opens use read-only immutable mode. The original supplied file is opened for reading only; it is never chmodded or written.

Activation/rollback reverify installed bytes before replacing `activation.json` atomically. Locks serialize operator writes; files/directories are fsynced. The pointer carries `publication_authorized=false`, a generation, active version and previous version. Repeated activation of the same version preserves the rollback target. Installed receipts are integrity evidence only, never serving authorization.

The runtime consumes `DAV_AI_PHARMA_ARTIFACT_ROOT`, validates the pointer/receipt and pins the selected immutable path for process lifetime. New processes pick up activation/rollback; existing processes remain on their verified retained version, avoiding mixed evidence across multi-connection reads. Startup and each connection still use the shared release gate. Runtime checksum caching uses file identity; cold checks are serialized and the 4.83 GB file is not rehashed per request.

**Trust boundary:** Store ownership and parent directories must prevent untrusted writes. Supported storage must provide reliable POSIX locking, same-filesystem atomic rename and directory fsync. Hostile privileged filesystem writers, weak shared-storage semantics and target-provider durability have not been qualified. Copy object-store downloads onto a persistent local/attached volume first; SQLite does not read remote URLs.

## Private staging configuration

**VERIFIED:** `docker-compose.staging.yml` describes backend/frontend only, no published ports, an internal network, read-only container roots, read-only managed-store mount, non-root users, dropped capabilities and temporary writable directories. Required operator settings prevent accidental empty paths/origins. Frontend assets use same-origin API URLs and an internal Nginx proxy on port 8080 with access logs disabled.

Both images built from dataset-free source. A one-shot unprivileged backend container successfully validated startup/readiness against the real managed store mounted read-only in local validation mode. A one-shot staging-mode check against the same valid store refused startup. The private Nginx config passed `nginx -t` as UID 101 on a read-only root filesystem; its informational global `user` directive warning is harmless when already running non-root.

**Not deployed:** No Compose `up`, network-facing application service, cloud resource or provider infrastructure was launched. The private configuration intentionally uses `DAVAI_ENV=staging`; with the existing authorization guard it cannot serve data or become ready. This is installation/deployment architecture preparation, not hosted-serving approval. Private TLS ingress, operator access and a release-bound serving-authorization mechanism remain separate review work.

## Verification of original and installed artifacts

**VERIFIED:** Two real managed copies (`validation-a`, `validation-b`) were installed only under `/tmp/davai-install-verification/store`. Both independently passed installation verification and remained unapproved. The original artifact remains:

| Field | Result |
|---|---|
| Bytes | `4825108480` |
| SHA-256 | `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71` |
| SQLite user_version | `4` |
| Release ID | `dav-ai-pharma-v1-phase4b-communications-20261006` |
| Contract / policy | `dav-ai-pharma-release-v1` / `1.0.0` |
| Original publication receipt | `publication_validated=false`, unchanged in both original metadata copies |

The original artifact verifier passed after installation/lifecycle checks. No frozen database, regulatory archive, backup or prior evidence receipt was edited. All managed copies are outside the repository/source candidate. The source archive contains no dataset directory or database artifacts.

## Startup, readiness and publication gate

**VERIFIED:** Managed roots automatically enable strict FastAPI startup checking. Deployed modes are also strict; `DAV_AI_PHARMA_REQUIRE_READY_AT_STARTUP=1` enables strict checking for a direct local path. Missing/corrupt/incompatible/permission-denied files, invalid selection or unauthorized serving cause fixed startup failure before the process becomes ready.

`DAV_AI_PHARMA_ARTIFACT_ROOT` and `DAV_AI_PHARMA_RELEASE_DB` are mutually exclusive; an explicitly empty managed root is invalid. A missing/broken managed store cannot silently fall back to the repository SQLite artifact or PostgreSQL. Ordinary non-strict local development still separates `/health` liveness (200 without data) from `/ready` (503 without valid authorized data). Strict startup refusal means no HTTP service is started; it does not falsely report a healthy data-serving process.

Tests verify that search, identity, recalls, adverse events, timeline, shared evidence/coverage and PDF generation all remain denied through the same gate in production/staging/preview, even with a valid selected store. The temporary deployed-denial guard was not removed or weakened. Selection metadata and installation receipts cannot grant publication. An existing process's readiness checks its pinned artifact, not a newer activation pointer; deleting/corrupting its pinned bytes fails closed, while a metadata change alone requires restart to take effect.

## Recovery and rollback

Exact installation, verification, activation, recovery and rollback commands are in [OPERATIONS.md](OPERATIONS.md). Core operator commands are:

```sh
PYTHONPATH=backend python scripts/manage_pharma_artifact.py install \
  --source /incoming/pharma.sqlite --root /srv/davai-artifacts --version release-v1-install-001
PYTHONPATH=backend python scripts/manage_pharma_artifact.py activate \
  --root /srv/davai-artifacts --version release-v1-install-001
PYTHONPATH=backend python scripts/manage_pharma_artifact.py inspect --root /srv/davai-artifacts
PYTHONPATH=backend python scripts/manage_pharma_artifact.py rollback-installed --root /srv/davai-artifacts
```

These are operator instructions, not commands executed against a deployed system during this task. Retain previous immutable copies; cutover/rollback affects new processes after a separately authorized restart.

A failed copy/hash/schema/permission check removes only its newly created incomplete copy. A crash can leave `.install-*`, which is never selectable; explicit `discard-incomplete` validates the identifier and contents before deletion. It never removes installed-version directories or broadly cleans the store.

Pre-replace activation failures leave the old pointer intact. A failure after atomic replace but before directory fsync can leave the new valid pointer already selected, with uncertain durability across power loss: inspect before retry/rollback. The implementation does not claim every I/O error implies no state change. Tests cover both boundaries. No half-written pointer or unverified target becomes eligible.

Corrupt/missing activation metadata requires explicit `recover-selection --root ... --version <known-version>`; that command re-verifies a retained installation and writes a fresh generation without inventing a rollback target. It refuses to replace healthy metadata. Corrupt/missing bytes or receipts must be replaced by a new verified installation label, never repaired in place. Legacy rehearsal `prepare/select/rollback --registry` commands remain separate; their `active.json` is not used by the runtime.

## Tests executed and limitations

| Check | Observed result |
|---|---|
| New installation/recovery regressions | **34 passed** |
| Final dataset-free source backend suite | **473 passed, 33 skipped, 7 deselected** (17.01 s) |
| Required pharmaceutical release gate against managed installed copy | **7 passed, 344 deselected**, no skipped critical checks (11.05 s) |
| Real-copy lifecycle, fresh processes | Startup A → selection B while A stayed pinned → restart selected B → rollback/restart selected A; readiness/search/evidence/PDF succeeded, approval false throughout |
| Missing/wrong artifact, unsupported identity/schema/tables, sidecars | Refused in controlled tests |
| Permission failure, invalid/conflicting configuration, malformed/missing selection | Startup/readiness failed closed; no fallback |
| Failed install rename and pre-replace activation | Incomplete copy cleaned / prior pointer retained |
| Post-replace fsync error | Valid new pointer inspectable, previous version retained; ambiguous outcome documented |
| Managed read-only container mount / unapproved staging startup | Local lifecycle ready / hosted staging lifecycle correctly refused |
| Both private-staging images from source-only export | Built successfully; no datasets/private .env files in context |
| Private Compose/Nginx checks | No ports, internal network, read-only mounts/roots confirmed; unprivileged Nginx config valid |
| Python compile/imports and git diff --check | Passed |
| Original artifact verification | Exact expected checksum/size/identity; approval false |

The 33 source-only skips are **27 pre-existing optional PostgreSQL ingestion tests** and **6 research-cohort tests** without their external fixtures. PostgreSQL was not started or introduced as a dependency for this task/application. Seven real-release checks were explicitly deselected in the source-only suite and then run separately as a required managed-artifact gate. Skips/deselections are not counted as passing integration evidence. The required gate still fails missing/corrupt artifacts, empty critical selection or skipped critical checks.

Real lifecycle checks used fresh subprocesses and FastAPI TestClient without starting an HTTP server. PDF responses were generated in memory with synthetic report names. Fault-injection tests used small synthetic SQLite files and monkeypatched expected checksums only within tests; production constants and real-copy verification remained exact. Real managed copies were independently hashed with the unmodified supported release contract.

Frontend application code did not change. Its production build was checked through both source-only Docker builds; this installation-only pass did not rerun browser/React unit suites from the prior authoritative candidate report. Private proxy traffic/TLS/ingress, provider storage durability, Linux amd64 acceptance, OS-image scanning and load/soak tests remain unverified. A Starlette test-client deprecation warning remains and is not a failing test.

## Source and files changed

Two independently generated source archives were byte-identical:

- Archive: `/private/tmp/davai-install-final-source-a.tar.gz`
- SHA-256: `78196f4c01d932167505d071d137c4d166b099931b663c78eb1f356085a9c68a`
- 260 source files; extracted root `/private/tmp/davai-install-final-source`

All exported hashes were compared to current source. This report and new verification receipts intentionally sit outside the source archive so recording evidence does not alter its identity. No bit-for-bit Docker image reproducibility claim is made; input dependency hashes/base-image digests and successful source-only builds are verified.

Added:

- `backend/app/db/pharma/artifact_store.py`
- `backend/tests/pharma_release/test_artifact_installation.py`
- `docker-compose.staging.yml`
- `ops/staging/nginx.conf`, `ops/staging/environment.example`
- `docs/staging-artifacts/OPERATIONS.md`, this report and verification receipts

Modified:

- `backend/app/db/pharma/release_connection.py`: managed resolution, immutable SQLite and sidecar rejection
- `backend/app/main.py`: strict managed/deployed lifespan checks
- `scripts/manage_pharma_artifact.py`: install/activate/inspect/rollback/recovery CLI and operator diagnostics
- `scripts/prepare_release_candidate.py`: include managed-install architecture/source, exclude generated receipts/report
- `.dockerignore`: package runtime store reader
- `backend/.env.example`: managed-root/startup settings
- `README.md`, current architecture, prior artifact operations: links and lifecycle semantics

The current branch remains `chore/stabilize-davai-v3`, HEAD `4ca92a94a6c27799c3ead5b0b00a91a3afb6fa03`. Existing uncommitted work remains intact, as does recovery branch `recovery/pharma-before-simplification-20261021` (`0e4c5112f0075199d98bc0436b0f890b5b3b2a11`). A pre-installation source snapshot/manifest was saved under /tmp without changing Git. No destructive Git command or index rewrite was used.

## Remaining blockers and exact next deployment action

**The installation subsystem is ready for reviewed private staging integration; hosted serving is still blocked.** Publication metadata remains false and staging/production startup remains denied. This is an intentional, verified blocker, not an installer failure. No integrity/selection operation authorizes a public launch.

The next task is to review this source candidate and the installation/lifecycle receipts, choose the target persistent POSIX volume/private ingress and runtime ownership policy, and separately authorize a tested release-bound private-serving policy that is at least as safe as the present denial gate. Then, in a separately authorized target validation environment, install the externally supplied artifact with the documented verify/install/activate commands and rerun the required seven-check gate and real browser journey before any rollout.

**Do not run the staging Compose `up` or deploy now.** The current blueprint deliberately refuses unapproved hosted startup. No provider provisioning, application launch, approval-flag change or source commit is authorized by these results. Public deployment remains **NO-GO**.
