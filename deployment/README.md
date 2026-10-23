# Deny-only deployment foundation

These files do **not** make Dav AI usable on the internet. They are an isolated health/denial application, a build-only frontend artifact, and private/default-disabled Terraform templates. They never import the pharmaceutical application or local agent API. No cloud deployment is authorized.

The dual-mode frontend was staged, not committed, when this foundation was implemented. Keep that existing index untouched and obtain a reviewed application commit before treating any image as a release candidate.

## Local checks only

From the repository root, using existing development dependencies:

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/deployment_foundation -q
actionlint .github/workflows/gcp-foundation.yml
```

With Terraform 1.13.5 and network access for the hash-pinned provider (these commands do not use a GCP backend or apply resources):

```bash
terraform -chdir=deployment/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=deployment/gcp validate
terraform -chdir=deployment/gcp test
```

The tests use a **mock Google provider** and `command = plan`. They do not perform a real GCP plan, authenticate, create resources or approve deployment. The default `foundation_enabled=false` selects zero resources. Do not run real cloud plan/apply commands in this milestone.

## Container builds

Use the repository root as context. Dockerfile-specific ignore files override the restrictive existing root context for these two builds only.

```bash
docker build --platform linux/amd64 -f deployment/foundation/Dockerfile -t davai-foundation:test .
docker build -f deployment/frontend/Dockerfile -t davai-ui-artifact:test .
```

The deny API uses a digest-pinned Python base, a small hash-locked ASGI server dependency set, a numeric non-root user and no evidence/model/auth SDK. Its `/health` returns 200 when configuration is valid; **all other paths return 503**, including `/ready`, research, catalog, session and batch paths. Health is process liveness, not pharmaceutical readiness.

The frontend image runs `npm ci` and the existing TypeScript/Vite production build, then copies only `dist` to a scratch artifact stage. It has no server, command or exposed port. The built local SPA still targets loopback and must not be advertised as a functional hosted application. The build excludes local environment files, tests and evidence fixtures; it does not bake a cloud URL or credential into the UI.

For an authorized **local-only** smoke check, publish only loopback and keep runtime restrictions:

```bash
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=512m --cpus=1 --pids-limit=64 \
  -p 127.0.0.1:18081:8080 davai-foundation:test
```

Do not publish on all host interfaces, mount the database, pass cloud keys, or point this image at Ollama. Stop the specific smoke container when finished. The application requires `DAVAI_ENV=staging|production` and `DAVAI_FOUNDATION_MODE=deny`; these are baked defaults, not an option to serve. It rejects data/key-file/model configuration and still denies business routes even if an unrelated publication variable is set.

## Infrastructure and credentials

`gcp/main.tf.json` pins Google provider 8.8.0, with reviewed platform hashes in `.terraform.lock.hcl`. Even if explicitly enabled in a future authorized operation, it describes only a private Artifact Registry repository, a runtime service account without project roles and a private/IAM-required deny-only Cloud Run service. There are **no public invoker grants, data buckets, model endpoints, secrets, queues, databases, WIF bindings or API-enablement resources**. Enabling these templates is not authorization to create infrastructure. An existing approved project, APIs and immutable reviewed deny-image digest would first be required.

The service account and registry precede a service image operationally: a future owner must provision approved registry/identity dependencies and publish a reviewed image before service creation, or split that bootstrap into reviewed modules. No placeholder image is deployed automatically. Do not treat a single initial apply as an approved bootstrap plan.

Cloud resources, hosted auth, durable sessions/jobs, model adapters and public frontend wiring are **design only**. The current CI workflow has read-only repository permissions, no OIDC minting, secrets or cloud calls, and does not push images or deploy. Local scans and verification limits are recorded in [the foundation report](../docs/deployment/GCP_MLOPS_FOUNDATION_REPORT.md).
