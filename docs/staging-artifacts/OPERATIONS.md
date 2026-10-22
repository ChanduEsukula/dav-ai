# Managed staging artifact installation and recovery

This is a provider-neutral, POSIX filesystem installation system. It does not deploy or provision a service. **Publication remains false and hosted staging/production serving remains denied.** The private Compose file is a prepared architecture, not authorization to launch it.

## Architecture and trust boundary

An offline operator copies the externally supplied release into a persistent store. The API mounts that store read-only; it never installs, activates, repairs or deletes files. Use reliable local/persistent POSIX storage with advisory locks, atomic same-filesystem rename and directory fsync. Download object-store artifacts to a local operator path before installation; do not point SQLite at remote object URLs. Weak-locking/shared filesystems need separate qualification.

```text
/srv/davai-artifacts/                    operator-writable, mode 0755
  .lock                                 operator-only, mode 0600
  activation.json                       atomic selection, mode 0644
  releases/
    <installation-version>/             immutable directory, mode 0555
      pharma.sqlite                     independent copy, mode 0444
      receipt.json                      exact integrity contract, mode 0444
    .install-<id>/                      incomplete, never selectable
```

Only the operator can write the store or its parent directories; the runtime UID needs traversal/read permissions only. No credentials, names, ages or report files belong here. Store receipts contain no original source paths. No existing installation is ever overwritten. Installation labels distinguish copies/generations of the currently supported exact release; arbitrary future release/schema versions are not accepted.

The shared runtime gate still denies production/staging/preview before database access. A local validation process can use a managed root. It pins its selected version for its lifetime; changing activation affects **new processes only**. Restart/cut over after activation to avoid mixing evidence across a multi-read request. Old processes may finish against their retained immutable version. Readiness checks the pinned artifact, not a newer pointer. Missing/corrupt pinned bytes or invalid permissions fail readiness. Missing/corrupt selection affects new startup; an existing healthy pinned process is not redirected.

## Exact release contract

- Release ID: `dav-ai-pharma-v1-phase4b-communications-20261006`
- Contract: `dav-ai-pharma-release-v1`; policy: `1.0.0`
- Supported SQLite user_version: `4`; all 19 required tables, including formulations
- Bytes: `4825108480`
- SHA-256: `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`
- `publication_validated`: **false**, unchanged

The installer streams a new copy, checks the source signature and streamed digest, fsyncs, then rehashes and verifies the copied schema/manifest/tables before publishing its immutable directory. Activation and rollback rehash/reverify again. SQLite sidecars (-wal/-shm/-journal) are refused; runtime/installation verification opens standalone immutable read-only SQLite. A malformed file cannot provide different logical contents through an unverified WAL. No source file is chmodded or written.

Runtime cold hashes are serialized/cached by current device/inode/size/timestamps. The 4.83 GB database is not hashed on every request. Deployment authorization never comes from a receipt or `activation.json`; all selection metadata is explicitly false for publication.

## Operator installation commands — do not run against production without authorization

Use Python 3.13 with the hash-locked runtime dependencies. Run from the reviewed source root; replace the absolute paths with operator-controlled paths. Do not put private operator environment files in Git.

```sh
python -m pip install --require-hashes -r backend/requirements-runtime.lock
PYTHONPATH=backend python scripts/manage_pharma_artifact.py verify \
  --database /incoming/pharma.sqlite
PYTHONPATH=backend python scripts/manage_pharma_artifact.py install \
  --source /incoming/pharma.sqlite --root /srv/davai-artifacts --version release-v1-install-001
PYTHONPATH=backend python scripts/manage_pharma_artifact.py inspect --root /srv/davai-artifacts
PYTHONPATH=backend python scripts/manage_pharma_artifact.py activate \
  --root /srv/davai-artifacts --version release-v1-install-001
```

Provide at least 4.83 GB per retained installation plus space for one pending copy; two retained versions require at least 9.65 GB in the store, excluding incoming artifacts, logs and filesystem overhead. Provision extra operational headroom. Check that the intended container UID can read the mounted store. Do not alter the original frozen release's permissions or bytes.

For a subsequent independently verified copy of the same supported release:

```sh
PYTHONPATH=backend python scripts/manage_pharma_artifact.py install \
  --source /incoming/pharma.sqlite --root /srv/davai-artifacts --version release-v1-install-002
PYTHONPATH=backend python scripts/manage_pharma_artifact.py activate \
  --root /srv/davai-artifacts --version release-v1-install-002
```

`activate` is idempotent for the already-active version and retains the prior rollback target. Only after a separately authorized serving policy and process restart will hosted application traffic be possible. No `up`, restart or deployment command is authorized by this document.

## Local validation, startup and readiness

Configure **one** of `DAV_AI_PHARMA_ARTIFACT_ROOT` (managed store) or `DAV_AI_PHARMA_RELEASE_DB` (legacy direct local read), never both. An explicitly empty managed-root setting is invalid and cannot fall back to the repository artifact.

Managed stores automatically require an artifact/authorization check in FastAPI startup. `DAV_AI_PHARMA_REQUIRE_READY_AT_STARTUP=1` also enables strict startup for a direct path. Hosted environment modes are strict by default. A failed check raises a fixed startup error and the process does not become ready; no request can fall back to PostgreSQL or a different database. In ordinary local development without strict startup, missing data leaves `/health` live and `/ready` at 503. Liveness contains no data-authorization assertion. Strict hosted startup currently refuses even a correct artifact because publication is not authorized.

For local validation only (not a hosted-mode override):

```sh
DAVAI_ENV=local DAV_AI_PHARMA_ARTIFACT_ROOT=/srv/davai-artifacts PYTHONPATH=backend \
  python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q
```

Use the existing outbound-blocked loopback server and `PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release` for the real browser gate. Selecting release tests with no data fails; the required gate also rejects skips and empty selections. Source-only tests must explicitly deselect `release_artifact` and do not qualify installation.

## Rollback

Retain the previous immutable directory and receipt. Rollback re-verifies before changing the pointer:

```sh
PYTHONPATH=backend python scripts/manage_pharma_artifact.py inspect --root /srv/davai-artifacts
PYTHONPATH=backend python scripts/manage_pharma_artifact.py rollback-installed --root /srv/davai-artifacts
```

A new process then pins the restored version; existing processes remain pinned until a controlled restart/cutover. For a specific older retained installation, use `activate --root ... --version <known-version>`. Never edit the SQLite file or replace an installed version in place. The old `prepare/select/rollback --registry` commands are legacy offline rehearsals; their active.json is not consumed by this managed system.

## Failed installation, activation and recovery

Pre-publication copy/checksum/schema/permission failures remove only that operation's new pending directory and leave installed versions and activation unchanged. A process killed before cleanup may leave `.install-*`; these names cannot be activated. Inspect first, then discard only the explicitly identified incomplete installation:

```sh
PYTHONPATH=backend python scripts/manage_pharma_artifact.py inspect --root /srv/davai-artifacts
PYTHONPATH=backend python scripts/manage_pharma_artifact.py discard-incomplete \
  --root /srv/davai-artifacts --name .install-abcdefgh
```

Discard refuses installed-version names, symlinks and unexpected contents. Unknown pending files require operator review; the tool does not perform a broad cleanup. Retry installation under a new version label after resolving disk or permission failures.

A failure before activation's atomic replacement preserves the previous pointer. An I/O/fsync error **after** replacement is ambiguous for durability: the selected pointer may already be the new, verified version. Inspect it before retrying or rolling back; never assume every error means no change. Readers see complete old/new JSON, never a half-written pointer. A runtime with an existing pin remains on its prior bytes until restart.

Missing/corrupt activation metadata fails new startup and never falls back. To restore selection from an independently retained and reverified installed version:

```sh
PYTHONPATH=backend python scripts/manage_pharma_artifact.py recover-selection \
  --root /srv/davai-artifacts --version release-v1-install-001
```

Recovery refuses to replace a healthy selection; normal activation should be used then. Recovery creates a fresh generation with no guessed rollback target. Restore another known version with explicit `activate` if needed. If bytes/receipts are corrupt or missing, install a newly supplied exact release under a new label and activate it; do not repair in place or forge receipts. Recovery grants no publication approval.

## Private staging architecture, not deployment

`docker-compose.staging.yml` has no published ports, an internal-only network, read-only artifact bind, read-only container roots, non-root processes, dropped capabilities and temporary writable directories. Frontend requests are same-origin and proxied privately; access logs are disabled. Provider-specific private TLS ingress/operator access, host policy and resource budgets remain to be reviewed separately.

Configuration validation/build commands only:

```sh
DAV_AI_STAGING_ARTIFACT_ROOT=/srv/davai-artifacts \
DAV_AI_STAGING_ORIGIN=https://exact-private-origin.example.invalid \
  docker compose -f docker-compose.staging.yml config --quiet
DAV_AI_STAGING_ARTIFACT_ROOT=/srv/davai-artifacts \
DAV_AI_STAGING_ORIGIN=https://exact-private-origin.example.invalid \
  docker compose -f docker-compose.staging.yml build
```

Do not run `up`: `DAVAI_ENV=staging` intentionally fails startup at the unchanged serving gate. This work makes installation/selection/recovery ready for controlled validation; it does not implement or approve hosted serving. A separately reviewed, release-bound authorization mechanism must meet or exceed the current gate before any staging-serving exception or public publication is allowed. The original `publication_validated=false` receipt remains untouched.
