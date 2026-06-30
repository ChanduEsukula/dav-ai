# DavAI Public Safety Intelligence — Source Expansion Checkpoint

**Checkpoint date:** June 25, 2026  
**Scope:** Source-expansion milestones through `fda-safety-communications-v1`  
**Status:** Validated portfolio prototype; not yet a production ingestion deployment

## 1. Executive Summary

DavAI has moved beyond a simple recall lookup experience into a multi-source public safety intelligence prototype. The latest expansion adds four distinct evidence layers—medical-device identity, vaccine adverse-event signals, foodborne outbreak context, and FDA medical-device safety communications—plus source freshness and provenance visibility.

The central product improvement is not merely “more data.” DavAI now preserves why a record exists and how it should be interpreted. A formal recall or enforcement action is different from a device identity record, an adverse-event report, an outbreak investigation, or an advisory. The source planner, normalized record contract, safety intelligence summary, identifier checks, and audit/freshness metadata work together to keep those distinctions visible.

This is a meaningful safety and engineering maturity step. DavAI can route a user’s query to relevant source families, normalize heterogeneous records into one response, report source failures without collapsing the whole search, retain payload hashes and pull metadata, and explain the evidence found in plain language.

The implementation remains intentionally prototype-scoped. The newly added UDI, VAERS, outbreak, and safety-communication adapters currently search small local curated/demo snapshots rather than continuously ingesting live upstream data. Results remain informational and must be verified against official sources.

> **Critical interpretation boundary:** Adverse-event reports, outbreak or investigation context, and safety communications are not proof of causation. They are not automatically recalls, and they must not be presented as evidence that every named product is defective, unsafe, or responsible for an event.

## 2. What DavAI Can Now Do

After these source expansions, DavAI can:

- Recognize medical-device searches such as `insulin pump`, `glucose meter`, and `CPAP`, then check device enforcement records alongside device-event signals, UDI identity records, and FDA advisory context.
- Detect a UDI-formatted identifier and use the openFDA UDI layer to help verify device identity, model, manufacturer, product code, and device identifier before comparing it with safety records.
- Recognize vaccine and vaccine adverse-event language and route it to a VAERS signal-report source without describing those reports as confirmed causal findings.
- Enrich food recall searches with CDC/FDA outbreak and investigation context, including pathogen, food vehicle, status, affected states, and reported illness outcomes.
- Retrieve FDA medical-device safety communication context for advisory-focused searches without automatically labeling the communication as a recall.
- Normalize different source formats into a shared record shape so results can be ranked, deduplicated, audited, and displayed together.
- Separate matched evidence into recall/enforcement, identity/reference, label, signal-report, outbreak-context, and other roles in the backend intelligence layer.
- Return a source-specific search plan, the sources checked, failed sources, records per source, audit records, payload hashes, and source-pull metadata.
- Show users when a source was checked and whether its payload metadata was stored, rather than presenting results as an unexplained black box.
- Continue returning partial results when one source fails or times out, while identifying the degraded source.

## 3. Source-by-Source Breakdown

### openFDA UDI Device Identity

**Milestone:** `openfda-udi-device-identity-v1` (`c9fdd14`)

The UDI expansion introduces an `openfda_udi_directory` registry entry, a dedicated adapter, query-understanding support for UDI identifiers, source-planner routing, database seed alignment, curated records, and route/planner/registry tests.

Its purpose is identity resolution, not recall detection. The normalized record can preserve device name, model, manufacturer, GMDN terminology, product code, distribution status, package count, and primary device identifier. A query such as `UDI 00312345678901` is detected as a medical-device query and returns an identity/reference record that can help the user verify the exact device before reviewing enforcement or adverse-event evidence.

**Why it matters:** Product names are often broad or ambiguous. Exact identifiers reduce the risk of applying a recall or advisory to the wrong model or device family.

**Current boundary:** The adapter searches a local curated/demo snapshot containing two records. Live openFDA UDI API ingestion is not yet implemented. The record itself is not evidence of a recall, defect, or safety problem.

### CDC VAERS Vaccine Signal

**Milestone:** `cdc-vaers-vaccine-signal-v1` (`0c46107`)

The VAERS expansion adds the `cdc_vaers` source, a vaccine query category, dedicated source planning, a VAERS adapter, normalized signal records, safety-summary role classification, curated records, database seed metadata, and focused tests.

The normalized record can carry the reported vaccine, manufacturer, symptoms, seriousness indicator, outcome, date, demographic context, narrative, and VAERS report identifier. The safety intelligence summary classifies matching VAERS records as signal reports.

**Why it matters:** Vaccine safety questions are not well served by recall-only search. A user may be asking whether an event was reported, not whether a product was recalled. DavAI can now represent that question without converting a report into a causal conclusion.

**Current boundary:** The adapter searches a local curated/demo snapshot containing three records. VAERS accepts reports without requiring proof that a vaccine caused the reported event. A VAERS report is not a recall, a verified diagnosis, or proof of causation.

### CDC/FDA Foodborne Outbreak Context

**Milestone:** `foodborne-outbreak-context-v1` (`194e357`)

This expansion adds the `cdc_foodborne_outbreaks` source, a dedicated adapter, food/outbreak query recognition, secondary-source planning, an `outbreak_context` intelligence-summary role, database seed alignment, curated records, and route/planner/registry tests.

Normalized outbreak context can include investigation ID, title, pathogen, food vehicle, agency, status, states, illness count, hospitalization count, death count, update date, summary, and official context URL.

**Why it matters:** Public safety decisions often develop before or outside a formal recall record. Investigation context can explain why a food or pathogen is receiving attention and can complement FDA or USDA enforcement records.

**Current boundary:** The adapter searches a local curated/demo snapshot containing three records. An outbreak investigation does not automatically establish that a particular branded product caused illness, and it is not automatically a formal recall.

### FDA Medical Device Safety Communications

**Milestone:** `fda-safety-communications-v1` (`f5a13c9`)

This expansion adds the `fda_safety_communications` registry source, adapter, medical-device query terms, source-planner inclusion, database seed metadata, curated records, and route/planner/registry tests.

Normalized safety communications can preserve communication ID, device/product area, manufacturer, publication date, risk context, recommended action, summary, and the official FDA source URL.

**Why it matters:** FDA may communicate emerging concerns, recommendations, monitoring information, or risk-mitigation guidance outside a classic enforcement record. Including this layer gives users a more complete view of official device-safety context.

**Current boundary:** The adapter searches a local curated/demo snapshot containing three records. A safety communication is advisory context; it is not automatically a recall and does not by itself prove that a device is defective or caused harm.

### Source Freshness API and UI

**Milestones:** `source-freshness-ui-v1` (`b74dbab`) and `source-freshness-api-v1` (`08e343d`)

The backend search response now includes a source-level freshness structure with:

- source ID, name, type, and kind;
- upstream status and returned-record count;
- a machine-readable freshness status and user-facing label;
- checked timestamp;
- snapshot status;
- source-pull ID; and
- source payload hash.

The statuses distinguish conditions such as `pulled_and_stored`, `checked_during_search`, `checked_no_records`, and `source_issue_reported`. The Public Safety UI exposes a source-freshness area in advanced source details and shows the check time, snapshot state, stored pull indicator, and payload-hash indicator.

**Why it matters:** Users and reviewers can see which sources participated in a search and whether DavAI captured auditable metadata. This improves trust, debugging, and operational review.

**Current boundary:** “Freshness” here primarily describes the status of the current check and stored provenance, not a complete production SLA or proof that upstream data is current. The backend emits the dedicated `source_freshness` array, while the current frontend display derives equivalent status from `sources_checked`, `source_audits`, and the retrieval timestamp. Direct frontend typing and rendering of the backend freshness contract is a sensible follow-up.

## 4. Evidence Types: What They Mean

| Evidence type | Primary question answered | Examples in DavAI | What it does **not** establish |
|---|---|---|---|
| Recall or enforcement record | Has an authority or responsible organization initiated a recall, correction, market action, or enforcement process? | openFDA drug, food, and device enforcement; CPSC; USDA FSIS; NHTSA | It does not mean every similar product or every unit is affected. Exact models, lots, dates, and identifiers still matter. |
| Identity or reference record | What exact product, drug, device, code, model, or label does the query refer to? | openFDA UDI, openFDA NDC, RxNorm, NHTSA vPIC | It is not a safety finding, recall, or evidence of harm. |
| Adverse-event signal report | Has an event been reported after use or exposure? | VAERS; openFDA device event | A report does not prove causation, incidence, prevalence, or product defect. It is not automatically a recall. |
| Outbreak or investigation context | Is a public-health agency investigating illnesses, a pathogen, or a possible food vehicle? | CDC/FDA foodborne outbreak context | Investigation context does not automatically prove that a specific product caused illness and is not automatically a recall. |
| Advisory or safety communication context | Has an agency published risk information, recommendations, or a safety notice? | FDA medical-device safety communications | An advisory is not automatically an enforcement action, product defect finding, or recall. |

These distinctions are the core of the project’s safety posture. DavAI is designed to support verification and triage, not to collapse every safety-related record into a binary “safe/unsafe” answer.

## 5. Why This Is More Mature Than a Simple Recall Search App

A simple recall app typically accepts keywords, searches one recall dataset, and returns matching rows. DavAI now demonstrates a broader intelligence workflow:

1. **Understand the query.** It normalizes common wording, corrects selected typos, detects identifiers such as VIN, NDC, UPC, and UDI, and identifies likely safety domains.
2. **Plan the source search.** It selects relevant primary and secondary sources instead of querying every source indiscriminately.
3. **Retrieve through adapters.** Each source has a boundary that converts source-specific data into a shared contract.
4. **Preserve evidence roles.** Recall, reference, signal, investigation, and advisory records retain different meanings.
5. **Normalize and rank.** Heterogeneous records can be deduplicated, scored, date-sorted, and returned consistently.
6. **Generate a bounded summary.** The safety intelligence summary states what evidence was and was not found and includes explicit caveats.
7. **Expose provenance.** Source IDs, URLs, retrieval timestamps, upstream status, audit IDs, pull IDs, and payload hashes make the result inspectable.
8. **Fail partially and visibly.** Per-source timeouts and errors can be reported while other source results remain available.
9. **Encourage exact verification.** Identifier checks help users compare the result with an exact model, lot, campaign, package code, UDI, VIN, NDC, or UPC.

This design is safer because it reduces overgeneralization, distinguishes evidence strength, and makes uncertainty visible. It is more mature because source integration, orchestration, normalization, observability, and user-facing explanation are treated as separate engineering concerns.

## 6. Architecture Summary

### Registry

`backend/app/sources/registry.py` is the shared source catalog. It assigns stable source IDs, names, official endpoints, modules, descriptions, and update-cadence metadata. Registry entries are aligned with SQL seed data and guarded by registry/schema/source-route consistency tests.

### Adapters

Source adapters isolate source-specific retrieval, filtering, error handling, and normalization. The new UDI, VAERS, outbreak, and safety-communication adapters currently load local JSON snapshots, match the query, deduplicate records, and return a `SourceAdapterResult`.

### Normalized Records

`NormalizedSafetyRecord` provides a common shape for source name/type/URL, source kind, category, product and company fields, title, reason, hazard, remedy, publication date, identifier-like recall number, models/lots, payload hash, retrieval time, and record URL. This contract allows unlike sources to participate in one result pipeline while retaining explanatory text.

### Query Understanding

The query-understanding layer normalizes phrases such as `blood sugar monitor` to `glucose meter`, recognizes device, vaccine, food, consumer-product, drug, and vehicle terminology, and detects VIN, NDC, UPC, and UDI identifiers. It exposes corrections and hints in the API response.

### Source Planner

The source planner maps query intent to primary and secondary source IDs. Medical-device searches now fan out across enforcement, device-event, UDI, and safety-communication sources. Food searches include outbreak context. Vaccine searches route to VAERS. Ambiguous terms can trigger clarification rather than a broad and potentially misleading source sweep.

### Search Workflow

The workflow executes planned adapter calls concurrently, enforces per-source timeouts, collects successful and failed sources, persists audit and source-pull metadata, deduplicates results, ranks by match score or date, and returns partial results when appropriate.

### Safety Intelligence Summary

The summary layer groups matched and checked sources by evidence role, sets evidence-found flags, produces a plain-language explanation, suggests verification steps, and states that it does not invent missing recalls, certify safety, or provide medical or legal advice.

An observed follow-up is to make the role taxonomy fully symmetrical across backend and frontend: outbreak context has a dedicated backend role, while UDI identity and FDA safety communications still need first-class role treatment in the summary/UI rather than falling into a generic bucket in some views.

### Source Freshness and Provenance

Every completed source result can produce an audit event and stored source-pull metadata, including a stable payload hash. The freshness response translates technical state into user-facing labels, and the UI shows source check/provenance details. This is a strong foundation for future last-success, age, SLA, and stale-source monitoring.

## 7. Testing and Validation Summary

Latest reported validation results for this checkpoint:

| Validation | Result |
|---|---:|
| Backend pytest suite | **439 passed** |
| Frontend tests | **253 passed** |
| Frontend production build | **Passed** |

Focused coverage added across the milestones verifies:

- source registration and registry/schema consistency;
- UDI detection, medical-device planning, normalized identity output, identifier checks, and freshness metadata;
- vaccine query routing, VAERS signal classification, and causation caveats;
- foodborne outbreak routing, normalized investigation context, and outbreak-summary flags;
- FDA safety-communication routing and advisory language;
- source freshness labels, stored pull metadata, payload hashes, and check timestamps; and
- frontend visibility of source freshness and provenance details.

These are the latest supplied validation results. This documentation-only checkpoint did not alter application logic or rerun the full suites.

## 8. Portfolio and Interview Talking Points

### Apple

- Human-centered safety design: the product avoids flattening nuanced public records into alarming binary claims.
- Identifier-first verification supports precise, privacy-conscious user workflows.
- Progressive disclosure keeps provenance available without overwhelming the primary experience.
- Strong answer to “How did you design for user trust?”: clear boundaries, official links, exact identifiers, and visible uncertainty.

### Google

- Multi-source search architecture with query normalization, intent routing, concurrent retrieval, ranking, and partial-failure handling.
- Extensible source adapters and a shared normalized schema resemble practical search/federation infrastructure.
- Provenance and payload hashes make retrieval behavior observable and debuggable.
- Strong answer to “How would you scale relevance?”: source-aware ranking, entity resolution, evaluation datasets, and measured query expansion.

### Microsoft

- Registry-driven integration, typed API contracts, adapter boundaries, audit persistence, and schema consistency demonstrate enterprise platform thinking.
- Source-specific failures are isolated instead of becoming system-wide failures.
- The architecture is ready to evolve toward tenancy, role-based access, scheduled jobs, and operational dashboards.
- Strong answer to “How would you make this enterprise-ready?”: authentication, tenant isolation, policy controls, durable queues, monitoring, and deployment automation.

### NVIDIA

- The project creates a structured, provenance-rich safety corpus suitable for later retrieval, classification, entity matching, and summarization experiments.
- Normalization and evidence-role labeling are valuable prerequisites for trustworthy ML; GPU inference is not currently required or implemented.
- Strong answer to “Where would AI add value?”: semantic retrieval, cross-source entity resolution, duplicate clustering, trend detection, and evidence-grounded summaries with offline evaluation.

### Healthcare and Public-Safety Roles

- The system treats safety data as decision-support evidence, not diagnosis or causal proof.
- VAERS and device-event reports remain signals; outbreak records remain investigation context; communications remain advisories.
- Exact identifiers, provenance, official-source verification, and explicit limitations reduce the risk of false reassurance or unnecessary alarm.
- Strong answer to “How did you handle high-stakes data?”: preserve evidence type, expose uncertainty, avoid unsupported causality, and retain auditable source metadata.

## 9. Remaining Gaps and Roadmap

1. **Real live API ingestion where possible.** Replace the new local UDI, VAERS, outbreak, and safety-communication demo snapshots with validated live APIs, downloadable official datasets, or robust official-page ingestion. Preserve snapshot fallback and clearly label source mode.
2. **Authentication and tenancy.** Add identity, authorization, tenant isolation, saved-workspace ownership, and audit access controls before supporting organizational use.
3. **Deployment.** Establish repeatable backend/frontend/database deployment, environment management, migrations, smoke checks, and rollback procedures for the expanded workflow.
4. **Scheduled refresh jobs.** Add durable scheduled ingestion, retries, idempotency, validation, snapshot versioning, and backfill support.
5. **Monitoring and alerting.** Track last success, source age, schema drift, record-count anomalies, timeout rates, payload changes, and sustained failures. Alert operators without treating operational freshness as clinical urgency.
6. **Clearer UI evidence grouping.** Give recalls, identity/reference records, signals, outbreak context, and advisories distinct labels and visual groups. Add a first-class advisory role, align the frontend with the backend outbreak role, and classify UDI as identity/reference in summary views.
7. **Complete freshness-contract wiring.** Type and render the backend `source_freshness` payload directly in the frontend so the API and UI share one source of truth.
8. **Evaluation and data quality.** Expand fixtures beyond small demo datasets, add golden query sets, measure precision/recall by source type, and test misleading edge cases.

## 10. How to Demo This

Use Public Safety Search and narrate both the result and its evidence type:

| Search | What to show |
|---|---|
| `insulin pump` | Medical-device planning across enforcement, event signals, UDI identity, and FDA communications. Explain that the layers answer different questions. |
| `glucose meter` | Device query normalization/routing and the difference between a product family match and an exact model or identifier match. |
| `CPAP` | Device safety records plus advisory context; open advanced source details to show checked sources and provenance. |
| `FDA safety communication insulin pump` | FDA advisory context. State clearly that a communication is not automatically a recall. |
| `Salmonella outbreak peanut butter` | CDC/FDA investigation context, pathogen and food vehicle details, and the `outbreak_context` summary. State that investigation context does not prove a specific product caused illness. |
| `UDI 00312345678901` | UDI detection, device identity/reference output, and the identifier check. Explain that the UDI record helps identify a device but is not a recall. |
| `vaccine adverse event` | Vaccine intent routing and VAERS signal-report language. State that reported events do not prove a vaccine caused them. |

For each demo, finish by opening **Advanced source details** and pointing out:

- planned and checked sources;
- returned record counts;
- source status and check time;
- stored source-pull and payload-hash indicators;
- official source links; and
- the public-data disclaimer and limitations.

## 11. Milestones Reviewed

| Tag | Commit | Change |
|---|---|---|
| `source-freshness-ui-v1` | `b74dbab` | Added source freshness/provenance display to Public Safety details. |
| `source-freshness-api-v1` | `08e343d` | Added source freshness objects to the Real World Safety API response. |
| `openfda-udi-device-identity-v1` | `c9fdd14` | Added UDI identity/reference source support. |
| `cdc-vaers-vaccine-signal-v1` | `0c46107` | Added VAERS vaccine adverse-event signal support. |
| `foodborne-outbreak-context-v1` | `194e357` | Added CDC/FDA foodborne outbreak investigation context. |
| `fda-safety-communications-v1` | `f5a13c9` | Added FDA medical-device safety communication context. |

## Final Assessment

DavAI now demonstrates the shape of a credible public safety intelligence platform: source-aware planning, normalized multi-source retrieval, evidence-role separation, bounded summaries, exact-identifier support, partial-failure handling, and auditable provenance. Its strongest quality is not that it claims to know whether something is “safe,” but that it helps users understand what public evidence exists, what that evidence means, and what must still be verified.

The next milestone should convert the strongest prototype sources into monitored live ingestion while preserving the interpretive safeguards introduced here.
