# RealWorldSafety Query Understanding

This document explains the query-understanding layer behind Dav AI's
RealWorldSafety search workflow. It is written for reviewers, recruiters, and
interviewers who want to understand what the system does before it queries
official and public safety sources.

Latest reported backend test status: **391 backend tests passed**.

## Summary

RealWorldSafety query understanding is a deterministic preprocessing layer for
`/api/v1/real-world-safety/search`. It cleans up common user phrasing, corrects a
small set of known typos, detects likely identifiers, and records any expansion
terms that may help retrieve official/public records.

The feature is intentionally conservative:

- It does **not** create fake records.
- It does **not** create synthetic recalls.
- It does **not** certify that a product, drug, food, device, or vehicle is safe.
- Query expansion only helps retrieve official/public records that already exist
  in the configured source adapters.
- Expanded terms are returned as query-understanding metadata and are only counted
  as used when they produce additional records.

## Where It Lives

Primary implementation files:

- `backend/app/services/search_workflows/real_world_query_understanding.py`
- `backend/app/services/search_workflows/real_world_safety_search.py`
- `backend/app/services/search_workflows/safety_intelligence_summary.py`
- `backend/app/schemas/real_world_safety.py`

Primary tests:

- `backend/tests/test_real_world_query_understanding.py`
- `backend/tests/test_real_world_safety_route.py`

The query-understanding object is returned in the API response as
`query_understanding`, alongside the final `safety_intelligence_summary`.

## Request Flow

At a high level, the RealWorldSafety route does this:

1. Receives the raw user query.
2. Builds a `RealWorldQueryUnderstanding` object.
3. Uses the corrected `search_query` for the main source sweep.
4. Checks configured official/public sources through source adapters.
5. Runs fallback expansion searches for known drug brand/generic relationships.
6. Deduplicates and ranks returned records.
7. Builds a Safety Intelligence Summary from the records that were actually
   returned.

The key point is that query understanding changes how Dav AI searches. It does
not change the meaning of source records and does not generate records on its own.

## Typo Correction

The first layer corrects a small, explicit list of common misspellings. This is
not open-ended fuzzy matching and not an LLM rewrite. The implementation uses a
fixed dictionary of known corrections.

Examples include:

| User input | Normalized search query | Expansion metadata |
|---|---|---|
| `tylonal` | `tylenol` | `acetaminophen` |
| `acetominophen` | `acetaminophen` | none |
| `ibuprophen` | `ibuprofen` | none |
| `benedryl` | `benadryl` | `diphenhydramine` |
| `listerea` | `listeria` | none |

For `tylonal`, the API keeps the raw query as `tylonal`, records the correction
`tylonal → tylenol`, searches the corrected term `tylenol`, and also exposes
`acetaminophen` as a known related term.

## Brand-to-Generic Expansion

The second layer expands known drug brands to generic names. The original brand
is not replaced for the primary search unless it was also typo-corrected. The
generic term is added as an expansion candidate.

Examples:

| Brand query | Expansion term |
|---|---|
| `Tylenol` | `acetaminophen` |
| `Advil` | `ibuprofen` |
| `Motrin` | `ibuprofen` |
| `Benadryl` | `diphenhydramine` |
| `Claritin` | `loratadine` |
| `Ventolin` | `albuterol` |

This matters because official drug, label, and NDC records often use generic
names, ingredients, or structured terminology rather than only consumer-facing
brand names.

## Fallback Expansion Search

After the main RealWorldSafety source sweep, the workflow runs a fallback search
for each expansion term that differs from the primary search query.

Today, expansion searches are targeted at drug and drug-reference sources:

- `openFDA Drug Enforcement API`
- `RxNorm/RxNav API`
- `DailyMed SPL API`
- `openFDA Drug Label API`
- `openFDA NDC Directory API`

For example, `Advil` remains the main query, but `ibuprofen` is checked as a
fallback term. If `ibuprofen` returns additional official/public records, the
response records it in `query_understanding.expansion_search_terms_used` and the
Safety Intelligence Summary explains that Dav AI also checked `ibuprofen`.

Expansion search is retrieval support only. It does not imply that every
`ibuprofen` record is relevant to every `Advil` package, lot, dose, labeler, or
NDC. Users still need to compare the official record against the exact product.

## Joined-Word Cleanup

Users often type product categories as joined words or hyphenated words. The
query-understanding layer normalizes common examples into the wording used more
often by public records.

Examples:

| User input | Normalized search query |
|---|---|
| `airfryer` | `air fryer` |
| `air-fryer` | `air fryer` |
| `powerbank` | `power bank` |
| `carseat` | `car seat` |
| `babycarseat` | `baby car seat` |

For example, `airfryer` becomes `air fryer`, which improves matching against
CPSC consumer-product recall records without creating any new recall data.

## Common Wording Cleanup

The system also normalizes several everyday phrases into terms more likely to
appear in official records.

Examples:

| User input | Normalized search query |
|---|---|
| `blood sugar monitor` | `glucose meter` |
| `blood sugar meter` | `glucose meter` |
| `glucose monitor` | `glucose meter` |
| `CPAP machine` | `cpap` |
| `sleep apnea machine` | `cpap` |
| `e scooter` | `electric scooter` |
| `eye drop` | `eye drops` |

The `blood sugar monitor -> glucose meter` case is a good example of the product
intent: the user may not know the regulatory wording, but the system can still
search for the term that official medical-device records are more likely to use.

## VIN, NDC, and UPC Detection

Query understanding detects likely identifiers and returns them under
`detected_identifiers`.

### VIN

A VIN-like query is compacted to alphanumeric characters, uppercased, and checked
for the 17-character VIN shape while excluding the letters `I`, `O`, and `Q`.

Example:

- Input: `1hg cm82633a 004352`
- Detected VIN: `1HGCM82633A004352`

VIN-like input is also handled by the RealWorldSafety vehicle flow: Dav AI can
decode the VIN through NHTSA vPIC and then use the decoded make/model/year to
check NHTSA vehicle recall records.

### NDC

NDC detection looks for drug-code-like input. If the query contains `ndc`, or if
the compacted query uses hyphens, and the digit count is between 9 and 11, the
system returns the compact digits as a likely NDC.

Example:

- Input: `NDC 66715 6547`
- Detected NDC: `667156547`
- Detected UPC: `null`
- Query type hint: `drug`

This does not certify that a particular package is affected by a recall. It only
helps the response preserve the likely identifier and classify the query.

### UPC

UPC detection looks for 12-, 13-, or 14-digit numeric input when the query is not
an NDC query.

Example:

- Input: `0 36000 29145 2`
- Detected UPC: `036000291452`
- Detected NDC: `null`
- Query type hint: `consumer_product`

The current implementation does not provide complete UPC, NDC, lot, serial, or
package-level resolution. Users must still compare official records against the
exact product label, package, lot, NDC, UPC, VIN, model, or serial number.

## Query Type Hints

After normalization, the system infers lightweight query type hints. These hints
are derived from detected identifiers, normalized text, and expansion terms.

Current hint categories include:

- `drug`
- `food`
- `medical_device`
- `consumer_product`
- `vehicle`
- `unknown`

These hints are response metadata. They help explain what the query looked like
to the system, but they do not override source records and do not certify that a
returned record applies to the user's exact item.

## Safety Intelligence Summary

The Safety Intelligence Summary is built after retrieval, using only returned
official/public records and checked source metadata. It is not a generative claim
about the outside world.

The summary returns:

- `query_type`
- `recall_or_enforcement_found`
- `reference_or_label_found`
- `signal_report_found`
- `matched_sources_by_role`
- `checked_sources_by_role`
- `top_result_titles`
- `expansion_explanations`
- `plain_language_summary`
- `suggested_next_steps`
- `caveat`

The caveat is intentionally explicit:

> This summary is generated only from returned official/public records. It does
> not invent missing recalls, certify safety, or provide medical/legal advice.

## Source Roles

RealWorldSafety separates sources by role so the UI and API can distinguish
different kinds of evidence.

### Recall / Enforcement

These sources can return recall, enforcement, public notice, or safety action
records:

- `CPSC Recalls API`
- `FDA Recalls, Market Withdrawals & Safety Alerts`
- `openFDA Food Enforcement API`
- `USDA FSIS Recall API`
- `openFDA Drug Enforcement API`
- `openFDA Device Enforcement API`
- `NHTSA Recalls API / datasets`

These are the first records users should inspect when a potential recall or
enforcement match exists.

### Reference Identity

These sources help identify a product, drug, vehicle, or code. They are not
recall sources by themselves:

- `RxNorm/RxNav API`
- `openFDA NDC Directory API`
- `NHTSA vPIC VIN Decoder API`

Reference identity records can help confirm active ingredient, NDC, labeler,
dosage form, route, vehicle make/model/year, or other identity fields before a
user compares against official recall records.

### Label Reference

These sources provide label/reference context, not recall decisions:

- `DailyMed SPL API`
- `openFDA Drug Label API`

They can help users compare drug label details, active ingredients, warnings,
usage sections, dosage forms, and route information against the product they have.

### Signal Report

Signal sources provide adverse-event or signal context. They are not recalls and
do not prove causation:

- `openFDA Device Event API`

The Safety Intelligence Summary treats signal reports separately so the product
does not accidentally frame adverse-event reports as official recall findings.

## Worked Examples

### `tylonal`

1. Raw query: `tylonal`
2. Typo correction: `tylonal → tylenol`
3. Primary search query: `tylenol`
4. Expansion term: `acetaminophen`
5. Query type hint: `drug`

The correction helps retrieve official/public drug and label records. It does
not create a Tylenol recall and does not certify that any Tylenol product is safe
or unsafe.

### `Advil`

1. Raw query: `Advil`
2. Normalized query: `advil`
3. Primary search query remains the brand term.
4. Expansion term: `ibuprofen`
5. Fallback expansion search checks `ibuprofen` against drug and drug-reference
   sources.

If `ibuprofen` returns additional records, `ibuprofen` appears in
`expansion_search_terms_used` and in the summary's expansion explanations.

### `blood sugar monitor`

1. Raw query: `blood sugar monitor`
2. Phrase cleanup: `blood sugar monitor → glucose meter`
3. Query type hint: `medical_device`

This improves retrieval from medical-device enforcement and device-event records
that use `glucose meter` wording.

### `airfryer`

1. Raw query: `airfryer`
2. Joined-word cleanup: `airfryer → air fryer`
3. Query type hint: `consumer_product`

This improves CPSC consumer-product recall matching for air fryer records.

### `NDC 66715 6547`

1. Raw query: `NDC 66715 6547`
2. Detected NDC: `667156547`
3. Detected UPC: `null`
4. Query type hint: `drug`

The system preserves the likely NDC so reviewers and UI code can explain what was
detected. It still does not guarantee package-level recall applicability.

## Why This Matters

Real users rarely search with perfect regulatory vocabulary. They type brand
names, common phrases, misspellings, joined words, partial identifiers, and
consumer shorthand. Public safety records often use different language:

- brand vs generic drug names,
- `glucose meter` vs `blood sugar monitor`,
- `air fryer` vs `airfryer`,
- VIN-derived vehicle identity vs raw vehicle text,
- NDC/reference records vs recall/enforcement records.

This feature matters because it improves retrieval while preserving trust
boundaries. Dav AI can be more forgiving of user input without pretending to know
facts that are not present in the official/public records.

For an interviewer or reviewer, this is the key engineering point: the system
uses deterministic query understanding to increase recall of relevant source
records, then keeps provenance, source role, caveats, and next steps visible.

## Limitations

- The typo and phrase maps are fixed dictionaries, not comprehensive fuzzy search.
- The system does not currently use an LLM for query rewriting.
- Brand-to-generic expansion is limited to known entries in the code.
- Fallback expansion search currently targets drug and drug-reference sources,
  not every source category.
- VIN detection is shape-based; vehicle recall matching still depends on NHTSA
  decoding and recall-source availability.
- NDC and UPC detection preserves likely identifiers but does not provide
  complete identifier-resolution, package-level, lot-level, or serial-level
  matching.
- A reference identity or label record is not a recall record.
- A signal report is not a recall and does not prove causation.
- Local curated snapshots may not represent every current public record.
- If an upstream source fails or times out, the response can be partial.
- No-match results do not certify safety; they only mean Dav AI did not find a
  matching public record in the checked sources for that search.

## Reviewer Notes

When reviewing this feature, look for these properties:

- The raw query is preserved as `raw_query`.
- Corrections are visible in `query_understanding.corrections_applied`.
- The actual retrieval term is visible as `query_understanding.search_query`.
- Expansion candidates are visible as `query_understanding.expanded_terms`.
- Expansion terms are only marked used if they returned additional records.
- Identifier detection is explicit under `detected_identifiers`.
- Source roles are separated in `safety_intelligence_summary`.
- The response caveat states that Dav AI does not invent missing recalls or
  certify safety.

That combination is what makes the feature useful without overstating what the
data can prove.
