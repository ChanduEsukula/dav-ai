# ProductScan OCR v2 Experimental Plan

**Status:** Planning only  
**Implementation status:** Not implemented  
**Scope:** Experimental OCR intake for the existing Dav AI safety workflows

ProductScan OCR v2 is a proposed input-assistance layer for Dav AI. This
document does not describe a production-ready feature, medical device, product
safety classifier, or autonomous matching system.

## 1. ProductScan Purpose

ProductScan should reduce the friction of manually typing product-label
information into Dav AI.

The feature would let a user provide a product-label image, extract visible
text, review candidate product information, and explicitly choose whether to
continue to:

- Pharmacy Safety
- Food Safety
- Cosmetic Safety

ProductScan should reuse the existing routed workflows. It should not become a
fourth safety-data system or introduce a separate safety conclusion.

## 2. What the Feature Will Do

ProductScan is intended to:

1. Accept one product-label or package image.
2. Validate basic file type and size constraints.
3. Run OCR against the image.
4. Return extracted text with OCR confidence metadata when available.
5. Identify bounded candidate fields such as product name, brand, ingredient,
   NDC, UPC, lot number, expiration date, and package size.
6. Mark every extracted field as unconfirmed.
7. Let the user edit, remove, or confirm extracted text.
8. Suggest a likely destination workflow using transparent label terms.
9. Require the user to confirm the text and destination before navigation.
10. Pass only the confirmed search query into the selected canonical workflow.

The OCR response should be treated as a draft transcription. Candidate
identifiers should be treated as possible values, not verified product
identity.

## 3. What the Feature Will Not Do

ProductScan must not:

- determine whether a product is safe or unsafe
- provide medical advice, diagnosis, treatment, or medication guidance
- tell a user to start, stop, or change a medication
- confirm that an OCR identifier belongs to the photographed product
- claim that a product matches a recall based on OCR alone
- infer causation from adverse-event reports
- identify a person, patient, purchaser, or prescriber
- automatically submit OCR output to a safety workflow
- silently replace user-entered or OCR-extracted text
- guarantee complete or accurate label extraction
- persist uploaded images by default
- provide production alerts, monitoring, or emergency guidance

An empty downstream search result must not be presented as evidence that a
product is safe.

## 4. Safety Boundaries

The ProductScan interface should state:

> OCR extracts visible label text and possible identifiers. It does not verify
> product identity or determine whether a product is safe. Review and confirm
> all text before searching public records.

Required boundaries:

- The user must confirm extracted text before routing.
- The user must select or confirm the destination workflow.
- Low-confidence fields must be visibly labeled.
- Illegible fields must remain blank or be marked "Could not read."
- The system must not invent missing identifier digits.
- The system must not infer a complete NDC, UPC, lot, or expiration value from
  a partial value.
- Public-record results must retain their existing source, audit, and safety
  wording.
- Pharmacy OCR must not expose medication-change recommendations.
- FAERS and cosmetic-event results must remain reporting signals, not causation
  claims.
- Uploaded images should be processed ephemerally unless a future, separately
  reviewed retention policy is introduced.

The upload screen should warn users not to include:

- patient names
- prescription numbers
- addresses or phone numbers
- insurance information
- payment-card information
- membership identifiers
- private medical records

If potentially sensitive text is detected, the safest initial behavior is to
warn the user and avoid returning that field as a search candidate.

## 5. Backend Route Proposal

The first proposed route is:

```text
POST /api/v1/product-scan/extract
Content-Type: multipart/form-data
```

This route is a proposal only. It is not implemented by this task.

Proposed request:

- `image`: one JPEG, PNG, or WebP image
- `workflow_hint`: optional `pharmacy`, `food`, or `cosmetic`

Proposed response:

```json
{
  "scan_id": "temporary-request-id",
  "status": "review_required",
  "extracted_text": "Visible OCR text...",
  "text_confidence": 0.82,
  "candidate_fields": [
    {
      "field": "product_name",
      "value": "Example Product",
      "confidence": 0.88,
      "confirmed": false
    }
  ],
  "candidate_workflow": "food",
  "workflow_reason": "Label contains food and nutrition terms.",
  "warnings": [
    "OCR output may be incomplete or incorrect.",
    "Confirm all text before searching public records."
  ],
  "image_retained": false
}
```

The extraction route should not call Pharmacy Safety, Food Safety, or Cosmetic
Safety automatically.

After user confirmation, the frontend can navigate through the existing route
model:

```text
?page=food-safety&q=<confirmed query>&raw_q=<original OCR candidate>
```

A separate confirmation API is not required for the first bounded prototype
unless server-side scan auditing or temporary state becomes necessary. The
smallest design keeps confirmation in frontend state and invokes existing
search routes only after an explicit user action.

## 6. Frontend UX Proposal

ProductScan should be a small experimental entry point, not a large homepage
hero.

Proposed flow:

1. User opens ProductScan.
2. User sees upload guidance and privacy warnings.
3. User selects or captures one label image.
4. The interface shows an image preview and an "Extract label text" action.
5. A loading state explains that OCR is reading visible text only.
6. The review screen displays:
   - editable extracted text
   - candidate product name
   - candidate brand
   - candidate identifiers
   - field-level confidence labels
   - possible workflow and explanation
7. The user corrects or removes incorrect values.
8. The user checks a confirmation control such as:
   - "I reviewed this text and want to use it as a public-record search."
9. The user selects Pharmacy, Food, or Cosmetic Safety.
10. The primary action becomes:
    - "Continue to Food Safety"
11. Dav AI navigates to the selected canonical page with the confirmed query.

The review step should use plain labels such as:

- High OCR confidence
- Review recommended
- Could not read
- User confirmed

It should not use labels such as:

- Verified product
- Exact recall match
- Safe product
- Unsafe product
- AI-approved

## 7. OCR Provider Options

Provider selection should be based on accuracy, privacy, latency, cost,
operational complexity, and confidence metadata.

### Local or Self-Hosted Options

**Tesseract OCR**

- Mature and widely understood.
- Works without sending images to a cloud OCR provider.
- Requires image preprocessing and careful handling of rotated or stylized
  labels.
- Confidence and layout behavior may be weaker on difficult packaging.

**EasyOCR or PaddleOCR**

- Potentially stronger on varied fonts and scene text.
- Adds model/runtime dependencies and deployment weight.
- Must be evaluated offline before any production route is proposed.

### Managed Cloud Options

**Google Cloud Vision**

- Strong general label and scene-text extraction.
- Managed confidence and bounding-box output.
- Introduces cloud credentials, cost, data-processing review, and vendor
  dependency.

**AWS Textract**

- Strong document-oriented extraction and structured blocks.
- Product packaging may not match its strongest document use cases.
- Introduces AWS operational and privacy requirements.

**Azure AI Vision / Document Intelligence**

- Supports OCR and layout extraction.
- Requires Azure credentials, cost controls, and data-processing review.

### Recommended Evaluation Path

1. Build an offline benchmark set of non-sensitive sample labels.
2. Evaluate Tesseract as a lightweight baseline.
3. Compare one managed provider only if the baseline is insufficient.
4. Record extraction accuracy by field type, not only full-text similarity.
5. Select a provider only after privacy, retention, latency, and cost review.

No provider should be added to production routes during the planning phase.

## 8. Data Extraction Fields

Candidate fields should remain intentionally bounded:

| Field | Examples | Notes |
|---|---|---|
| Product name | "Strawberry Protein Powder" | Primary confirmed search candidate |
| Brand | "Example Nutrition" | Optional search context |
| Active ingredient | "Metformin hydrochloride" | Pharmacy only when visible |
| Strength | "500 mg" | Context only; not dosing advice |
| NDC candidate | "12345-6789-10" | Preserve formatting and confidence |
| UPC candidate | "012345678905" | Validate shape/check digit where possible |
| Lot or batch | "LOT A1234" | Never infer missing characters |
| Expiration date | "EXP 06/2027" | Label transcription only |
| Package size | "60 tablets", "12 oz" | Search/verification context |
| Manufacturer or distributor | "Example Labs" | Optional source comparison field |
| Ingredient text | Visible ingredient list | May be long; user selects useful terms |
| Product category | drug, food, cosmetic, unknown | Transparent rule-based suggestion only |

Raw OCR text should be retained in the response long enough for user review,
but image retention should remain disabled by default.

## 9. Identifier Parsing Plan

Identifier parsing should be deterministic and conservative.

### Processing Order

1. Preserve the raw OCR line.
2. Normalize whitespace without removing meaningful separators.
3. Detect nearby label prefixes such as `NDC`, `UPC`, `LOT`, `BATCH`, or `EXP`.
4. Generate candidate values with character offsets or bounding-box references.
5. Apply format validation.
6. Assign a parser confidence separate from OCR confidence.
7. Require user confirmation.

### NDC Candidates

- Accept common 10-digit and 11-digit segmented presentations.
- Preserve hyphens as observed.
- Do not automatically convert a 10-digit candidate to 11 digits in the first
  prototype.
- Do not claim that a syntactically valid NDC exists in an official directory.

### UPC Candidates

- Accept bounded UPC-A/EAN-like numeric candidates.
- Use check-digit validation where the format supports it.
- Treat failed check-digit validation as a warning, not a corrected value.
- Do not promise exact UPC recall lookup unless an existing public source
  explicitly supports it.

### Lot and Batch Candidates

- Prefer values adjacent to explicit `LOT` or `BATCH` labels.
- Preserve letters, numbers, hyphens, and slashes.
- Avoid extracting ordinary dates or package counts as lot numbers.
- Never fill missing or uncertain characters.

### Expiration Candidates

- Detect values adjacent to `EXP`, `USE BY`, or similar terms.
- Preserve the displayed date.
- Avoid converting ambiguous dates without user confirmation.

## 10. Testing Plan

### Unit Tests

- file type and size validation
- text normalization
- NDC candidate parsing
- UPC candidate parsing and check-digit behavior
- lot/batch parsing
- expiration parsing
- sensitive-field warning rules
- workflow suggestion rules
- confidence-label thresholds

### Backend Contract Tests

- valid image returns `review_required`
- unsupported file types are rejected
- oversized images are rejected
- OCR provider failure returns a bounded error
- no image is retained by default
- extracted fields default to `confirmed: false`
- extraction never invokes a safety search route
- logs and errors do not contain image bytes or sensitive OCR text

### Frontend Tests

- upload and preview states
- extraction loading and failure states
- editable OCR text
- unconfirmed fields cannot be submitted
- keyboard-accessible field review
- workflow selection is explicit
- route navigation uses only confirmed text
- safety wording remains visible
- no safe/unsafe conclusion appears

### Offline Evaluation

Use a versioned, non-sensitive benchmark containing:

- medication boxes without patient labels
- food and supplement packaging
- cosmetic packaging
- rotated labels
- low-light images
- glare and curved containers
- small print
- partial labels

Track:

- character error rate
- word error rate
- exact field accuracy
- identifier precision and recall
- false identifier extraction rate
- workflow suggestion accuracy
- low-confidence calibration

Deep-learning experiments must remain under an offline experiment directory and
must not be imported by FastAPI routes or frontend production code.

## 11. Rollout Plan

### Phase 0: Planning

- Approve safety wording and proposed contract.
- Build a non-sensitive evaluation set.
- Define image privacy and retention requirements.

### Phase 1: Offline OCR Evaluation

- Compare local OCR baselines.
- Evaluate field-level accuracy.
- Test identifier parsers independently.
- Do not expose an API route or frontend entry point.

### Phase 2: Internal Extraction Prototype

- Add a feature-flagged extraction route.
- Use ephemeral processing.
- Return review-required output only.
- Add audit-safe operational metadata without storing image contents.

### Phase 3: Local Demo UX

- Add a small ProductScan page or modal.
- Require explicit text confirmation.
- Route only to existing canonical workflows.
- Keep the feature labeled "Experimental."

### Phase 4: Limited Portfolio Demo

- Use prepared, non-sensitive sample packaging.
- Monitor OCR errors and correction behavior.
- Show the confirmation boundary before any safety search.

### Phase 5: Production Readiness Review

Production consideration requires:

- privacy review
- provider retention review
- abuse and upload-security review
- cost and latency limits
- accessibility review
- observability without sensitive payload logging
- field-level accuracy thresholds
- rollback and feature-flag controls

## 12. Demo Script

1. Open ProductScan and state:

   > ProductScan is an experimental label transcription tool. It does not
   > determine whether a product is safe.

2. Upload a prepared, non-sensitive food label.
3. Select "Extract label text."
4. Show the raw OCR text and candidate fields.
5. Point out a low-confidence or editable field.
6. Correct one field manually.
7. Explain:

   > OCR output is never treated as verified product identity. The user reviews
   > every value before searching public records.

8. Confirm the text.
9. Select Food Safety.
10. Continue to the existing Food Safety page.
11. Show that the downstream page retains public-source and no-safety-guarantee
    wording.
12. Close with:

    > ProductScan improves input convenience. Dav AI's existing workflows,
    > public sources, provenance, and safety boundaries remain responsible for
    > the actual record review.

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| OCR reads a product name incorrectly | Show editable text and require confirmation |
| Identifier digits are confused | Preserve raw text, show confidence, validate format, never invent digits |
| User interprets OCR as verification | Label all fields as candidates until confirmed |
| User interprets search results as a safety verdict | Retain existing no-safety-guarantee and public-record wording |
| Sensitive information appears in an image | Warn before upload, detect likely sensitive fields, avoid image retention |
| Image data appears in logs | Prohibit image bytes and full OCR payloads from routine logs |
| Cloud provider retains images | Review provider settings and contracts before integration |
| Provider outage blocks scanning | Return a bounded extraction error; preserve manual search |
| Large or malicious uploads consume resources | Enforce content type, file size, dimensions, timeouts, and request limits |
| Workflow suggestion is wrong | Explain the suggestion and require user selection |
| Lot/UPC/NDC parsing creates false confidence | Separate format validity from official identity and recall matching |
| Deep-learning experiment leaks into production | Keep experiments offline with no production-route imports |
| Portfolio demo overclaims readiness | Keep "Experimental" and "Planning/Prototype" labels visible |

## Decision Summary

ProductScan OCR v2 should be implemented only as a review-first input layer.
Its responsibility ends after extracting visible text and candidate
identifiers. The user remains responsible for confirming the text and choosing
the relevant canonical workflow.

No OCR output, identifier candidate, workflow suggestion, or downstream
zero-result response may be used to declare a product safe or unsafe.
