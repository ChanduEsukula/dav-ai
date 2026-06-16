# Vector Storage Implementation Plan

## Purpose

This document plans a future vector storage implementation for Dav AI documentation chunks.

It is planning-only. It does not implement pgvector, migrations, database tables, vector storage code, real embedding calls, OpenAI calls, RAG, generated answers, or frontend behavior.

The goal is to define a careful path from the current deterministic documentation retrieval foundation toward future semantic retrieval over Dav AI's own documentation.

## Current State

Dav AI already has a safe documentation foundation:

- static documentation search through `GET /api/v1/docs/search`
- deterministic documentation chunking through `GET /api/v1/docs/chunks?max_results=<n>`
- a backend embedding interface for documentation chunks
- deterministic fake/local embedding previews for tests and internal preview only
- no real vector database
- no pgvector migration
- no real embedding provider calls
- no LLM-generated answers
- no RAG behavior

The current system searches and previews allowlisted repository documentation only. It does not make product, drug, food, supplement, cosmetic, medical, or safety decisions.

## Non-goals

This plan does not include:

- real OpenAI calls in this stage
- production RAG
- pgvector implementation in this stage
- database migrations in this stage
- vector storage runtime code in this stage
- user-uploaded document embedding
- ProductScan image or OCR embedding
- private health data or PHI
- diagnosis, treatment guidance, or medical advice
- automatic product safety determinations
- autonomous recall matching
- generated answers without citations
- replacement for FDA, USDA, openFDA, or official source workflows

## Product And Safety Constraints

Vector storage, if added later, must remain documentation-oriented.

Required constraints:

- documentation search only
- no medical advice
- no safety verdicts
- no generated answers unless citations are present
- official FDA, USDA, openFDA, and source workflow records remain authoritative
- vector retrieval must not replace source-backed safety APIs
- zero retrieved docs must not imply a product is safe
- retrieved docs must not be treated as complete source coverage
- ProductScan OCR text must not become verified product identity
- any future answer layer must say when information is unavailable

Vector retrieval may support source guidance, glossary lookup, documentation discovery, and education. It must not decide whether a product, drug, food, supplement, or cosmetic is safe or unsafe.

## Staged Implementation Path

### Stage 1: Database Capability Check And Feature Flag

Add a runtime and deployment capability check before any storage work.

Design requirements:

- introduce a disabled-by-default feature flag such as `DOCS_VECTOR_STORAGE_ENABLED`
- check whether the configured database supports the required extension and vector dimension
- expose capability status through internal diagnostics only if needed
- keep current docs search and chunks endpoints operational when vector storage is disabled
- make local development safe when pgvector is unavailable

The feature flag should gate ingestion, retrieval, and any future vector-backed route. A missing extension must not break normal Dav AI safety workflows.

### Stage 2: pgvector Extension Migration Plan

Plan a migration that enables pgvector only after the deployment target is confirmed.

Migration considerations:

- verify pgvector availability in Supabase or the target PostgreSQL environment
- use an idempotent extension creation pattern where supported
- document rollback behavior, including what happens if extension creation is unsupported
- keep migration independent from safety workflow tables
- avoid enabling vector retrieval until ingestion and tests are ready

This stage should not add embeddings or retrieval behavior by itself. It only prepares database capability.

### Stage 3: `documentation_chunks` Table Design

Future table proposal:

```text
documentation_chunks
  id
  chunk_id
  source_path
  title
  section_heading
  line_start
  line_end
  text
  character_count
  content_hash
  embedding_provider
  embedding_model
  embedding_dimension
  embedding
  created_at
  updated_at
```

Column notes:

- `id`: database primary key.
- `chunk_id`: deterministic stable chunk identifier from source path, line range, and content hash.
- `source_path`: repository-relative allowlisted path.
- `title`: document title derived from markdown.
- `section_heading`: nearest markdown heading for the chunk.
- `line_start` and `line_end`: source line range for citation and review.
- `text`: chunk text used for retrieval.
- `character_count`: deterministic chunk size metadata.
- `content_hash`: hash of chunk text for idempotent re-ingestion.
- `embedding_provider`: provider name, such as a future real provider or deterministic local provider.
- `embedding_model`: provider model name, if applicable.
- `embedding_dimension`: stored vector dimension.
- `embedding`: future vector column, likely `vector(<dimension>)` if pgvector is available.
- `created_at` and `updated_at`: operational timestamps.

Suggested indexes:

```text
unique(chunk_id)
index(source_path)
index(content_hash)
index(embedding_provider, embedding_model, embedding_dimension)
future vector index on embedding
```

The exact vector index type should be selected after corpus size and retrieval latency are measured.

### Stage 4: Ingestion And Backfill Command Design

Add a backend command only after the schema exists and feature flag behavior is settled.

Command responsibilities:

- read the same allowlisted docs used by static docs retrieval
- build deterministic chunks using the existing chunking service
- compute or request embeddings through the embedding provider interface
- upsert by `chunk_id`
- compare `content_hash` to skip unchanged chunks
- update changed chunks idempotently
- delete or mark stale chunks whose source files or line ranges no longer exist
- emit counts for inserted, updated, skipped, stale, and failed chunks

The command should support a dry-run mode before writing to the database.

Example future command shape:

```text
python -m app.jobs.ingest_documentation_chunks --dry-run
python -m app.jobs.ingest_documentation_chunks --apply
```

No user-uploaded documents, OCR images, private files, source code, tests, migrations, or env files should be ingested.

### Stage 5: Semantic Retrieval Endpoint Design

Only after storage and ingestion are tested, add a bounded retrieval endpoint.

Possible route:

```text
GET /api/v1/docs/semantic-search?q=<query>&max_results=<n>
```

Response should return cited chunks, not generated answers:

```text
query
results
  chunk_id
  source_path
  title
  section_heading
  snippet or text
  line_start
  line_end
  content_hash
  score
limitations
```

Required behavior:

- validate query length
- cap `max_results`
- return no-results state honestly
- cite source paths and line ranges
- include documentation-only limitations
- never replace FDA, USDA, openFDA, or existing public-record search workflows
- fall back cleanly when vector storage is disabled or unavailable

Hybrid search can be evaluated later by combining deterministic keyword search with vector retrieval, but the initial retrieval endpoint should stay simple and inspectable.

### Stage 6: Bounded Cited Answer Layer, If Ever Added

A cited answer layer is optional and should come only after retrieval evaluation.

If added, it must:

- answer only from retrieved documentation
- include citations for every substantive claim
- say when information is unavailable
- refuse or redirect medical advice and safety verdict requests
- avoid product-specific claims
- avoid diagnosis or treatment guidance
- never infer safety status from retrieved docs
- route users back to official FDA/USDA/source workflows for public-record verification

This stage would still not be a safety decision system.

## Operational Concerns

### Feature Flag

Use a disabled-by-default flag for vector storage and retrieval. The app must continue to run with the flag off.

### Idempotent Ingestion

Ingestion should be safe to run repeatedly. `chunk_id` and `content_hash` should drive upsert behavior.

### Content Hash Based Re-ingestion

If chunk text changes, `content_hash` changes. The ingestion command should update the stored row and embedding metadata. Unchanged chunks should be skipped.

### Source Allowlist

Vector ingestion must use the same allowlist as static docs retrieval unless a separate reviewed allowlist is explicitly approved.

Allowed examples:

- `README.md`
- `docs/architecture/*.md`
- `docs/demo/*.md`
- `docs/productscan/*.md`
- `docs/operations_runbook.md` if present

Excluded examples:

- source code
- migrations
- tests
- env files
- private files
- node_modules
- user uploads
- OCR images or raw OCR payloads

### Rollback Strategy

Rollback should be clear before deployment:

- disable the feature flag
- stop ingestion jobs
- keep static docs search available
- rollback table/index migrations if needed
- preserve or delete experimental rows according to the environment policy

### pgvector Availability

Supabase/Postgres environments may differ. Before migration:

- verify extension availability
- verify vector dimension support
- verify index creation support
- verify local development setup
- document behavior when pgvector is unavailable

### Local Development Fallback

If pgvector is unavailable locally, Dav AI should support:

- static docs search
- docs chunk preview
- deterministic embedding preview
- no vector-backed storage or retrieval

Local fallback must not silently pretend vector retrieval is active.

### Tests Before Deployment

Do not deploy vector-backed retrieval until migrations, ingestion, route behavior, limitations, and rollback have automated tests.

## Testing Plan

Future implementation should include:

- migration tests if the project has migration test coverage
- database capability and feature-flag tests
- ingestion idempotency tests
- content hash and chunk ID stability tests
- stale chunk cleanup or tombstone tests
- source allowlist enforcement tests
- embedding metadata persistence tests
- retrieval ranking tests
- no-results tests
- disabled-feature fallback tests
- route validation tests
- safety limitation tests
- citation source path and line range tests
- regression tests proving public safety workflows still use source-backed APIs

Evaluation should include boundary prompts that ask for safety verdicts, medical advice, diagnosis, treatment guidance, product claims, or unsupported answers. These should be refused or redirected.

## Deployment Gate Checklist

Before enabling vector storage outside a development branch:

- feature flag exists and defaults off
- pgvector support is confirmed in target database
- migration rollback is documented
- ingestion dry run reports expected counts
- ingestion apply mode is idempotent
- source allowlist is enforced
- stored chunks include line ranges and content hashes
- retrieval route returns citations and limitations
- no generated answers are enabled
- official source workflows remain authoritative
- tests pass in CI

## Interview Talking Points

- Dav AI stages AI-adjacent infrastructure carefully instead of jumping straight to RAG.
- The system first built deterministic docs search, then deterministic chunks, then a fake embedding interface, and only then planned vector storage.
- Vector storage is for documentation retrieval and source education, not safety verdicts.
- `content_hash`, `chunk_id`, source path, and line ranges preserve provenance.
- Feature flags and idempotent ingestion keep the implementation reversible.
- Official FDA/USDA/openFDA workflows remain the source-backed authority for safety review.
