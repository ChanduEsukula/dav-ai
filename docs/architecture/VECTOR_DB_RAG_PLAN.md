# Vector DB / RAG Plan

## Purpose

This document outlines a future vector database and retrieval-augmented generation (RAG) capability for Dav AI.

The purpose is to improve explanation, glossary lookup, documentation retrieval, source guidance, and user education. A future RAG layer should help users understand Dav AI workflows, public-source limitations, terminology, provenance fields, and how to verify official FDA/openFDA or USDA records.

Vector DB/RAG must not decide whether a product, drug, food, supplement, or cosmetic is safe or unsafe.

## Non-goals

This plan does not include:

- medical advice
- safety verdicts
- diagnosis or treatment guidance
- product-specific claim generation
- replacement for official FDA/USDA notices
- private health data
- PHI
- autonomous recall matching
- LLM safety decisioning
- product, package, UPC, NDC, or lot-level safety determination
- automatic action recommendations based on retrieved text

## Recommended First Use Case

The recommended first use case is a bounded **Safety Guide Assistant** or **Source Help Assistant**.

The assistant would retrieve from Dav AI's own documentation, source explanations, glossary entries, and official-source interpretation notes. It would answer questions such as:

- What does an openFDA adverse-event report prove or not prove?
- What is the difference between a recall record and an adverse-event report?
- What does "not a safety guarantee" mean in Dav AI?
- How should a user verify a lot number, NDC, UPC, package size, or recall notice?
- What source metadata should be reviewed before acting?

The assistant should be educational only. It should guide users back to source records and existing Dav AI workflows rather than generating product-specific safety claims.

## Why Not Use RAG for Safety Verdicts

RAG can retrieve relevant text, but retrieval does not make the retrieved text complete, current, correctly matched, clinically meaningful, or applicable to a user's exact product.

Dav AI source workflows already include important limitations:

- public adverse-event reports do not prove causation
- public source data may be incomplete, delayed, duplicated, or difficult to interpret
- zero returned records do not prove a product is safe
- product identifiers can be ambiguous or transcribed incorrectly
- official notices must be checked against exact brand, package, lot, date, manufacturer, and source context

Using RAG to produce a safety verdict would blur these boundaries. It could also create false confidence by turning partial retrieval into a fluent answer. For that reason, RAG should support explanation and source guidance only. It should cite retrieved documents and say when information is unavailable.

## Candidate Knowledge Sources

Initial knowledge sources should be bounded and curated:

- Dav AI README and architecture docs
- ProductScan OCR plan and limitations
- source registry descriptions
- glossary entries for terms such as FAERS, CAERS, recall, enforcement, NDC, UPC, lot, adverse event, classification, and audit ID
- source interpretation notes for FDA/openFDA and USDA/FSIS workflows
- operations and demo docs that explain current product boundaries
- selected official FDA/USDA help pages or interpretation pages, only if licensing and update cadence are reviewed

Candidate sources should exclude:

- user-uploaded images
- private user data
- PHI
- raw OCR payloads by default
- uncontrolled web pages
- unreviewed forum or social-media text

## Architecture Options

### Option A: Postgres pgvector / Supabase Vector

Use Postgres with `pgvector`, or Supabase vector support if available in the deployed environment.

This is the recommended first production-aligned option because Dav AI already uses PostgreSQL/Supabase persistence patterns. It keeps retrieval metadata close to existing audit, source-pull, and application data practices.

Benefits:

- consistent operational stack
- easier provenance and document metadata joins
- simpler local and hosted deployment story
- clear migration path for document chunks, embeddings, and retrieval logs

Tradeoffs:

- requires schema design and migration planning
- requires embedding generation and refresh jobs
- may need indexing and performance tuning as corpus size grows

### Option B: Local In-memory Embeddings for Prototype

Use a local JSON or in-memory embedding index for a portfolio prototype.

Benefits:

- fast to prototype
- no database migration required
- easy to reset and inspect

Tradeoffs:

- not persistent
- not suitable for larger corpora
- weak auditability unless retrieval logs are separately captured
- not production-ready

### Option C: External Managed Vector DB Later

Use a managed vector database only after Dav AI has a clear corpus, evaluation plan, and operational requirements.

Benefits:

- managed scaling and vector search features
- potentially stronger hybrid search and filtering capabilities

Tradeoffs:

- adds vendor dependency
- adds privacy, retention, and cost review requirements
- may complicate provenance and audit metadata
- should not be introduced before the retrieval use case is proven

## Data Model Sketch

Future tables or collections could include:

```text
rag_documents
  id
  source_type              -- dav_ai_doc, glossary, official_source_note
  title
  canonical_url
  version
  owner
  reviewed_at
  created_at
  updated_at

rag_chunks
  id
  document_id
  chunk_index
  heading
  content
  embedding
  token_count
  checksum
  created_at
  updated_at

rag_retrieval_events
  id
  request_id
  user_question_hash
  retrieved_chunk_ids
  retrieval_strategy
  response_mode
  created_at
```

The model should preserve document source, version, reviewed timestamp, and chunk checksum. Retrieval event logging should avoid storing private user content by default.

## Retrieval Flow

Recommended retrieval flow:

1. User asks a source-help or glossary question.
2. The frontend sends the question to a bounded assistant endpoint.
3. The backend validates the request and rejects medical advice, safety verdict, diagnosis, treatment, or product-specific claim requests.
4. The backend embeds or normalizes the question for retrieval.
5. The retrieval layer searches approved Dav AI documents and glossary/source notes.
6. The assistant composes a short answer using only retrieved context.
7. The answer cites retrieved documents or sections.
8. If retrieval does not contain enough support, the answer says the information is unavailable.
9. The response includes boundaries such as "not medical advice" and "verify official FDA/USDA sources."

RAG answers must cite retrieved documents. They must not fabricate citations, infer missing facts, or answer beyond the retrieved corpus.

## Safety Boundaries

Future RAG behavior must preserve these boundaries:

- no safety verdicts
- no medical advice
- no diagnosis or treatment guidance
- no medication-change recommendations
- no autonomous recall matching
- no claims that a product is safe or unsafe
- no claims that an adverse-event report proves causation
- no claims that a zero-result search proves absence of risk
- no use of ProductScan OCR text as verified product identity
- no storage or retrieval over PHI or private health records
- no response without citations when citations are required
- clear "information unavailable" behavior when retrieved context is insufficient

The assistant should redirect users to existing Dav AI workflows for public-record searching and to official FDA/USDA sources for final verification.

## Evaluation Plan

Evaluation should happen before any user-facing RAG release.

Evaluation sets should include:

- glossary questions with known answers
- source interpretation questions
- boundary-pressure prompts asking for safety verdicts
- medical advice prompts
- product-specific claim prompts
- questions with no answer in the corpus
- citation accuracy checks
- stale or ambiguous source wording

Key metrics:

- citation precision
- grounded-answer rate
- refusal or redirect accuracy for unsafe/non-goal prompts
- unsupported-claim rate
- "information unavailable" accuracy
- user-edit and user-feedback patterns
- latency and retrieval stability

Manual review should inspect whether answers stay educational, cite sources, and avoid product-specific safety conclusions.

## Rollout Stages

### Stage 0: Planning Only

Document scope, non-goals, candidate sources, data model, and safety boundaries. No vector DB or RAG implementation exists in this stage.

### Stage 1: Static Docs Ingestion

Ingest a small, reviewed corpus of Dav AI documentation and architecture notes. Keep retrieval internal or behind a development flag.

### Stage 2: Source Glossary Retrieval

Add glossary and source interpretation notes. Prioritize explainability for FDA/openFDA, USDA/FSIS, FAERS, CAERS, audit metadata, and ProductScan limitations.

### Stage 3: Bounded Assistant Answers With Citations

Expose a Safety Guide Assistant or Source Help Assistant that answers only from retrieved documents. Require citations and explicit "information unavailable" behavior.

### Stage 4: Evaluation and Guardrails

Run adversarial boundary tests, citation checks, retrieval quality checks, and manual review. Add monitoring for unsupported claims, missing citations, and unsafe answer attempts.

### Stage 5: Optional Product-context Retrieval, Still No Safety Verdicts

Optionally allow retrieval of educational guidance based on a user-selected workflow context, such as explaining what fields to verify for a food recall or an NDC search. Even in this stage, RAG must not decide whether a specific product is safe or unsafe.

## Interview Talking Points

- Dav AI would use vector DB/RAG for education and source guidance, not safety decisions.
- The first recommended use case is a bounded Safety Guide Assistant or Source Help Assistant.
- Postgres pgvector or Supabase vector is the natural first architecture option because the project already uses PostgreSQL/Supabase patterns.
- RAG answers must cite retrieved documents and say when information is unavailable.
- The system should reject or redirect medical advice, diagnosis, treatment, safety verdict, and product-specific claim requests.
- ProductScan OCR text should remain user-reviewed input assistance, not verified product identity.
- Evaluation should measure grounding, citation accuracy, refusal behavior, unsupported claims, and boundary adherence before any public release.
- External managed vector databases can wait until the corpus, evaluation needs, and operational requirements justify them.
