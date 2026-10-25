# Independent review checklist — grounded pharmaceutical answers

**Status: PENDING.** This checklist prepares review; it does not supply judgments.
The reviewer must be someone other than the developer/AI author of the answers.
Clinical completeness should be assessed by a reviewer with suitable domain expertise.

Review the seven cases in
[`independent-review-packet-phase3b-v1.json`](evaluation/phase3b-v1/independent-review-packet-phase3b-v1.json).
Use its full `source_sections`, question, exact answer and citation metadata, not
just the quoted excerpts. Refer to the frozen original label and linked source as
needed; distinguish a newer online label version from the stored version.

For **each generated statement**, record a judgment and supporting source span:

- **Claim support:** Does the cited source actually support the statement in this
  question's context? Check negation, population, dose/formulation and uncertainty.
- **Citation identity:** Correct product/NDC, record, label set/version, section,
  character span, source date and URL? Can a reader open the intended text?
- **Question relevance:** Does the answer address the requested topic? Identify
  irrelevant, redundant or unanswered parts even when every quote is exact.
- **Missing qualifiers:** Is an antecedent, heading, interaction partner, exception,
  conditional phrase or nearby warning needed to avoid a misleading impression?
- **Scope:** Are ingredient-level FAERS associations being presented as causation,
  selected-NDC observations, incidence or personal risk? Are recall lot/package
  restrictions preserved? Label quotations do not authorize those conclusions.

For each case, provide: reviewer name/role, review date, per-statement support,
question relevance, missing context, source references and proposed disposition
(accept for demonstration / revise / abstain). Use **uncertain** where the available
source is insufficient. Avoid turning uncertainty into a positive support judgment.

Write the completed review to a **new, separately versioned file**. Do not overwrite
this checklist, the original packet, annotations, raw responses or existing results.
An exact source-text/citation check is a mechanical check, not a clinical judgment.

The original g03 and h01 support/relevance reviews also remain **PENDING**. Their
older `/private/tmp/dav-ai-phase3/followup/...` packets were absent during Phase 3B;
recover a retained copy if reviewing those original outputs. Reviewing the new
Phase 3B versions does not silently complete a different historical packet.

No independent support percentage is reported until actual reviewer judgments
exist, with their denominator, methodology and unresolved cases disclosed.
