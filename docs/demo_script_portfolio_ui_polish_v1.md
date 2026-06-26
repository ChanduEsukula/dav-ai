# DavAI Portfolio Demo Script: UI Polish v1

- **Checkpoint:** `portfolio-ui-polish-v1`
- **Latest commit:** `3c873f7 Polish Saved Searches user language`
- **Recommended length:** 5 minutes
- **Primary path:** Home -> Safety Record Search -> sample query -> evidence types -> source verification links -> Explain These Results -> Saved Searches

## One-Sentence Opener

DavAI helps people search selected public safety records, separate evidence types, verify official source links, and get a bounded explanation of the current results without turning public data into medical or legal advice.

## Recommended Demo Queries

- `air fryer`
- `Advil`
- `NDC 66715 6547`
- `Toyota Camry`
- `sunscreen`

Use `air fryer` first for a normal-user demo. Use `Advil` or `NDC 66715 6547` for a more technical interviewer because those queries show reference, label, recall, and identifier boundaries.

## 5-Minute Script

### 0:00 to 0:30: Home

Click: open the homepage.

Say:

> DavAI is a public-record safety search product. It is not trying to decide whether something is safe or unsafe. The core workflow is search, understand what kind of public evidence exists, verify official source links, and explain the result within strict limits.

Point out:

- Safety Record Search is the primary action.
- The app uses public records and source links.
- The boundary is visible: not medical advice, not a safety guarantee.

Do not spend time on advanced pages yet.

### 0:30 to 1:30: Safety Record Search

Click: the main Safety Record Search input.

Search:

```text
air fryer
```

Say:

> This is the normal user path. A person should be able to type a product, drug, vehicle, identifier, food, cosmetic, or brand and get routed into the right public-record workflow.

Point out:

- query routing
- example searches
- quick preview or handoff into the detailed Safety Record Search page
- public-record limitation language

Then click the detailed Safety Record Search result path.

### 1:30 to 2:30: Evidence Types Found

Click: result summary and the evidence-type section.

Say:

> The important design choice is that DavAI does not flatten every source into one scary warning. It separates recall or enforcement records from reference records, labels, signal reports, outbreak context, advisories, and other public records.

Point out:

- **Evidence types found**
- **Recall / enforcement** versus **reference / label** versus **signal reports**
- any source failures or missing data shown as source status rather than hidden errors

Good technical phrasing:

> The backend uses source adapters and role classification so heterogeneous records can be normalized while preserving what each source actually means.

### 2:30 to 3:15: Sources Checked and Verification Links

Click: source verification links or source details.

Say:

> DavAI is source-aware. The app is useful only if the user can verify the official record. So the result page keeps source names, source roles, checked status, and official links visible.

Point out:

- official/public source link
- source integration mode when visible
- source checked status
- exact identifiers to verify, such as NDC, UPC, VIN, model, lot, manufacturer, or date

Say:

> A no-result search is not a safety guarantee. It only means DavAI did not find a matching record in the selected public sources and current source state.

### 3:15 to 4:15: Explain These Results

Click: **Explain These Results**.

Ask one prompt:

```text
What evidence types were found?
```

Say:

> This is the AI-assisted part. It is intentionally bounded. The assistant receives structured context from the current result page, source metadata, audit ID, scores, and limitations. It is not browsing the web, not making medical judgments, and not full production RAG.

Point out:

- short answer
- source citations or audit context
- limitations
- refusal/safety boundaries if relevant

Good interviewer phrasing:

> I treated the assistant as an explanation layer over retrieved context, not as a decision-maker. That lets the product demonstrate AI usefulness while preserving source and safety boundaries.

### 4:15 to 5:00: Saved Searches

Click: **Saved Searches**.

Say:

> Saved Searches are the workflow extension. Instead of making users repeat the same public-record checks manually, the system can persist a repeatable search definition, run it manually, show run history, compare latest and previous counts or scores, and link back to audit records.

Point out:

- saved search definitions
- manual run
- latest/previous comparison
- audit link

Close with:

> The strongest engineering theme is source-aware product design: typed APIs, adapters, auditability, source verification, careful language, and a bounded assistant. The project is intentionally honest about what is public data, what is deterministic, and what is not production AI.

## What To Say To A Recruiter

Use this if the listener is non-technical:

> DavAI is a search-first public safety records app. It helps someone look up a product, drug, food, vehicle, or cosmetic, see what public records were found, open official source links, and ask for a plain-English explanation of the current results. It is careful not to give medical or legal advice.

Recruiter-friendly highlights:

- full-stack React + FastAPI project
- polished search-first product workflow
- source-backed results
- clear safety boundaries
- repeatable Saved Searches
- AI feature that explains current results without overclaiming

## What To Say To A Senior Engineer

Use this if the listener is technical:

> The architecture uses a source registry, adapter boundaries, normalized record contracts, source-role classification, fail-soft search orchestration, audit events, source-pull metadata, and a context-bounded assistant route. Most intelligence is deterministic by design; the assistant is an explanation surface over structured result context.

Senior-engineer highlights:

- heterogeneous source normalization
- source integration modes
- query understanding and identifier detection
- partial failure behavior
- audit and provenance
- typed FastAPI schemas and typed React clients
- front-end progressive disclosure
- conservative safety language

## What Not To Claim

Do not claim:

- DavAI determines whether something is safe or unsafe.
- DavAI provides medical advice, diagnosis, treatment guidance, legal advice, or official recall instructions.
- A missing result means no safety issue exists.
- Adverse-event reports prove causation or incidence.
- The assistant is full production RAG.
- DavAI has a production vector database-backed retrieval system.
- DavAI has production ML, a neural-network safety classifier, or clinical prediction model.
- ProductScan is production OCR safety verification.
- Curated snapshots are real-time integrations.
- Saved Searches are production alerting or fully scheduled user notifications.

Preferred wording:

> DavAI searches selected public records, separates evidence types, preserves source links, and uses a bounded assistant to explain the current result context. It supports verification; it does not make safety, medical, legal, or causation decisions.

## Backup Demo Paths

If `air fryer` is slow or sparse:

- Use `Advil` to discuss drug/reference/label boundaries.
- Use `NDC 66715 6547` to discuss identifier-first verification.
- Use `Toyota Camry` to discuss vehicle query paths.
- Use `sunscreen` to discuss cosmetic/personal-care routing.

If the assistant provider is not configured:

Say:

> The assistant route has a mock fallback unless a backend-only provider key is configured. That is intentional for local demo safety. The important part is the context contract and guardrails, not pretending every environment has a production LLM enabled.
