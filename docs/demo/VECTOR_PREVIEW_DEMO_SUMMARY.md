# Dav AI Vector Preview Demo Summary

## Current Checkpoint

- Git tag: `demo-vector-preview-june-2026`
- Backend tests: 345 passed
- Frontend tests: unavailable for this checkpoint. No completed user-provided frontend test run result was available to record, and an interrupted frontend run should not be counted as passed.

This checkpoint demonstrates Dav AI's staged path from public-record safety workflows into documentation retrieval infrastructure without adding production RAG or automated safety decisions.

## ProductScan Pipeline

```text
image upload
  -> image quality checks
  -> OCR readiness warnings
  -> browser OCR
  -> editable text review
  -> candidate extraction
  -> user-selected safety workflow
```

ProductScan remains an input-assistance workflow. It helps users review visible label text before routing a confirmed query to Pharmacy Safety, Food Safety, or Cosmetic Safety. It does not identify the product with certainty and does not determine whether anything is safe or unsafe.

## Docs And Vector Preview Pipeline

```text
static docs retrieval
  -> docs chunks
  -> embedding interface
  -> documentation_chunks schema
  -> idempotent ingestion
  -> semantic retrieval preview
```

The vector preview path is intentionally incremental. Dav AI first keeps documentation retrieval deterministic and inspectable, then adds chunk metadata, a fake/local embedding interface, metadata storage, idempotent ingestion, and finally a read-only semantic preview over stored preview embeddings.

## Safety Boundaries

- No medical advice.
- No safety verdicts.
- No real OpenAI embeddings.
- No pgvector yet.
- No generated RAG answers.
- Official FDA, USDA, openFDA, and source-backed workflows remain authoritative.
- Vector retrieval must not replace public-record safety APIs.
- ProductScan OCR and documentation retrieval are review aids only.

## Demo Script

1. Home page: Introduce Dav AI as a public-record safety review workspace, not a clinical or product-safety verdict system.
2. ProductScan OCR readiness: Upload a label image, show image quality checks and OCR readiness warnings, run browser OCR, then edit/review extracted text before selecting a workflow.
3. Help Docs Search: Show documentation snippets with source paths and limitations. Emphasize that it returns cited docs, not generated advice.
4. Backend docs semantic-preview endpoint: Call `GET /api/v1/docs/semantic-preview?q=<query>&max_results=<n>` and show ranked documentation chunks with line ranges, similarity scores, and limitations.
5. Audit/Sources page: Close with provenance: source names, audit metadata, retrieval context, and why official records remain the review authority.

## Interview Explanation

Dav AI uses staged retrieval and human review because public safety data is high-context, incomplete, and easy to overstate. Jumping directly to production RAG could make partial retrieval look like a confident answer.

The safer engineering path is layered:

- deterministic search before semantic preview
- source allowlists before broad ingestion
- chunk IDs, line ranges, and content hashes before vector storage
- fake/local embeddings before any real provider
- preview retrieval before generated answers
- explicit limitations at every step

That design shows restraint: Dav AI can explore AI-adjacent retrieval while keeping safety interpretation inside source-backed workflows and leaving final verification with official FDA/USDA/source records.
