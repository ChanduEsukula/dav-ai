import type { RecallSearchResponse } from '../api/recalls'
import type { DrugEventSearchResponse } from '../api/drugEvents'
import type { BriefingRole, SafetyBriefing } from '../types/briefing'

const unsafePhrases = [
  'stop taking',
  'start taking',
  'change your medication',
  'diagnosed with',
  'caused by this drug',
]

function highestRecallScore(data: RecallSearchResponse) {
  return data.results.reduce(
    (highest, result) =>
      result.risk_score.score > highest.risk_score.score ? result : highest,
    data.results[0]
  )
}

function roleSummary(role: BriefingRole, query: string) {
  switch (role) {
    case 'consumer':
      return `This briefing summarizes public safety-signal information for "${query}" in plain language for consumer review.`
    case 'pharmacy':
      return `This briefing summarizes public safety-signal information for "${query}" for pharmacy inventory and staff review workflows.`
    case 'clinic':
      return `This briefing summarizes public safety-signal information for "${query}" for clinic awareness and patient-facing communication planning.`
    case 'public_health':
      return `This briefing summarizes public safety-signal information for "${query}" for public-health or analyst review.`
  }
}

function roleChecklist(role: BriefingRole) {
  switch (role) {
    case 'consumer':
      return [
        'Compare the exact product name, brand, package, and lot details against the official source.',
        'Read the official FDA/openFDA source details before making assumptions.',
        'Contact a qualified clinician or pharmacist for personal medical decisions.',
      ]
    case 'pharmacy':
      return [
        'Check inventory for exact product, lot, manufacturer, and package matches.',
        'Document staff review of the public source record and internal inventory status.',
        'Escalate confirmed matches through the pharmacy’s normal safety and compliance workflow.',
      ]
    case 'clinic':
      return [
        'Prepare neutral patient-facing language based only on public source details.',
        'Share source limitations with staff so the signal is not treated as diagnosis or treatment guidance.',
        'Route patient-specific questions to qualified clinical staff.',
      ]
    case 'public_health':
      return [
        'Review source freshness, record count, and whether the signal is isolated or repeated.',
        'Track whether future source refreshes show changed record count or status.',
        'Preserve source/audit details for reproducibility.',
      ]
  }
}

function assertSafeText(text: string) {
  const normalized = text.toLowerCase()
  return !unsafePhrases.some((phrase) => normalized.includes(phrase))
}

export function generateRecallBriefing(
  data: RecallSearchResponse,
  role: BriefingRole
): SafetyBriefing {
  const topResult = data.results.length > 0 ? highestRecallScore(data) : null

  const whatWasFound =
    data.results.length > 0 && topResult
      ? [
          `${data.count} FDA recall record(s) matched the search.`,
          `Highest visible review signal: ${topResult.risk_score.label} (${topResult.risk_score.score}/100).`,
          `Top matched product: ${topResult.product_description ?? 'Unknown product description'}.`,
          `Recall reason: ${topResult.reason_for_recall ?? 'No reason provided in the source record'}.`,
        ]
      : [
          'No FDA recall records matched the current search.',
          'No-results output does not prove that a product is safe or unsafe.',
        ]

  const whatToVerify =
    data.results.length > 0 && topResult
      ? [
          'Verify exact product name, lot, package, manufacturer, and recall number in the official source.',
          `Review FDA classification and status: ${topResult.classification ?? 'Unknown class'} / ${topResult.status ?? 'Unknown status'}.`,
          'Confirm the source timestamp and audit ID before using the briefing in a workflow.',
        ]
      : [
          'Try searching by brand name, generic name, product category, ingredient, or manufacturer.',
          'Check official FDA sources directly if this is a time-sensitive safety concern.',
        ]

  const briefing: SafetyBriefing = {
    role,
    source: 'recall',
    title: `${roleSummary(role, data.query)}`,
    summary: roleSummary(role, data.query),
    whatWasFound,
    whatToVerify,
    suggestedReviewChecklist: roleChecklist(role),
    limitations: [
      'This briefing is generated from public recall search results only.',
      'A matched recall record may apply only to specific lots, packages, firms, dates, or distribution areas.',
      'No-results output does not prove absence of safety concerns.',
      'This briefing is not medical advice, diagnosis, or treatment guidance.',
    ],
    sourceDetails: {
      sourceName: data.source_name,
      endpoint: data.endpoint,
      retrievalTimestamp: data.retrieval_timestamp,
      auditId: data.audit.audit_id,
      recordCount: data.count,
    },
    disclaimer: data.medical_disclaimer,
  }

  const combinedText = [
    briefing.title,
    briefing.summary,
    ...briefing.whatWasFound,
    ...briefing.whatToVerify,
    ...briefing.suggestedReviewChecklist,
    ...briefing.limitations,
    briefing.disclaimer,
  ].join(' ')

  if (!assertSafeText(combinedText)) {
    throw new Error('Generated briefing contained unsafe medical wording.')
  }

  return briefing
}

export function generateDrugEventBriefing(
  data: DrugEventSearchResponse,
  role: BriefingRole
): SafetyBriefing {
  const topReaction = data.top_reactions[0]
  const leadingCategory = data.reaction_categories[0]
  const intelligence = data.intelligence_score

  const whatWasFound =
    data.top_reactions.length > 0
      ? [
          `${data.count} FAERS record(s) were reviewed for reporting-pattern context.`,
          `DrugSignal Intelligence score: ${intelligence.score}/100 ${intelligence.label}.`,
          `Review priority: ${intelligence.review_priority}. Data confidence: ${intelligence.data_confidence}.`,
          `Top reaction concentration: ${intelligence.top_reaction_concentration}%.`,
          leadingCategory
            ? `Leading reaction category: ${leadingCategory.category} (${leadingCategory.count} report mentions).`
            : 'No reaction category grouping was available for this result.',
          `Top reported reaction term: ${topReaction.reaction} (${topReaction.count} report mentions).`,
          'These are adverse-event reporting patterns only, not proof of causation.',
        ]
      : [
          'No FAERS drug-event records matched the current search.',
          'No-results output does not prove that a drug is safe or unsafe.',
          `DrugSignal Intelligence score: ${intelligence.score}/100 ${intelligence.label}.`,
          `Data confidence: ${intelligence.data_confidence}. Review priority: ${intelligence.review_priority}.`,
        ]

  const whatToVerify =
    data.top_reactions.length > 0
      ? [
          'Verify the drug name, brand/generic naming, and source query context.',
          `Review score version: ${intelligence.score_version}.`,
          `Review reaction classifier version: ${data.reaction_classifier_version}.`,
          'Review FAERS limitations before interpreting any reported reaction term or category.',
          'Do not treat reporting patterns as evidence that a drug caused an event.',
        ]
      : [
          'Try searching by generic name, brand name, active ingredient, or alternate spelling.',
          `Review score version: ${intelligence.score_version}.`,
          `Review reaction classifier version: ${data.reaction_classifier_version}.`,
          'Check official FDA/openFDA sources directly if this is a time-sensitive safety concern.',
        ]

  const briefing: SafetyBriefing = {
    role,
    source: 'drug_event',
    title: `${roleSummary(role, data.query)}`,
    summary: roleSummary(role, data.query),
    whatWasFound,
    whatToVerify,
    suggestedReviewChecklist: roleChecklist(role),
    limitations: [
      ...intelligence.limitations,
      'Reaction classification is rule-based and may group incomplete or ambiguous public adverse-event terms.',
      'FAERS reports may be incomplete, duplicated, delayed, or influenced by reporting behavior.',
      'This briefing is not medical advice, diagnosis, or treatment guidance.',
    ],
    sourceDetails: {
      sourceName: data.source_name,
      endpoint: data.endpoint,
      retrievalTimestamp: data.retrieval_timestamp,
      auditId: data.audit.audit_id,
      recordCount: data.count,
    },
    disclaimer: data.medical_disclaimer,
  }

  const combinedText = [
    briefing.title,
    briefing.summary,
    ...briefing.whatWasFound,
    ...briefing.whatToVerify,
    ...briefing.suggestedReviewChecklist,
    ...briefing.limitations,
    briefing.disclaimer,
  ].join(' ')

  if (!assertSafeText(combinedText)) {
    throw new Error('Generated briefing contained unsafe medical wording.')
  }

  return briefing
}