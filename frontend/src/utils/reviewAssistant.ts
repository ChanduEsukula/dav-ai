import type { RecallSearchResponse } from '../api/recalls'
import type { DrugEventSearchResponse } from '../api/drugEvents'
import { formatDate, formatTimestamp } from './recallFormatters'

export type AskDavAIModule = 'recall' | 'drug-event'

export type AskDavAIPrompt =
  | 'plain_english'
  | 'verify'
  | 'score'
  | 'source'
  | 'top_reactions'
  | 'faers_limits'

export type AskDavAIAnswer = {
  title: string
  summary: string
  bullets: string[]
  sourceDetails: string[]
  limitation: string
}

const unsafeQuestionPatterns = [
  /should\s+i\s+(stop|start|take|use|change)/i,
  /is\s+.*safe\s+for\s+me/i,
  /do\s+i\s+have/i,
  /did\s+.*cause\s+my/i,
  /what\s+treatment/i,
  /what\s+dose/i,
  /dosage/i,
  /diagnos/i,
  /emergency/i,
]

export function isUnsafeMedicalQuestion(question: string) {
  return unsafeQuestionPatterns.some((pattern) => pattern.test(question))
}

export function generateUnsafeMedicalAnswer(): AskDavAIAnswer {
  return {
    title: 'I can explain public data, but not give medical advice',
    summary:
      'DAV AI can help explain public FDA/openFDA information, source details, and what fields to verify. It cannot provide medical advice, diagnosis, treatment guidance, personal risk assessment, or medication instructions.',
    bullets: [
      'For personal medical decisions, contact a qualified clinician or pharmacist.',
      'For product-specific recall instructions, verify the official FDA/source record.',
      'For urgent symptoms or emergencies, seek appropriate emergency care.',
    ],
    sourceDetails: ['No source result was used for this refusal.'],
    limitation: 'Public-data review help only. Not medical advice.',
  }
}

function recallTopResult(data: RecallSearchResponse) {
  return [...data.results].sort((left, right) => right.risk_score.score - left.risk_score.score)[0]
}

export function generateRecallAssistantAnswer(
  data: RecallSearchResponse,
  prompt: AskDavAIPrompt,
  question = ''
): AskDavAIAnswer {
  if (question && isUnsafeMedicalQuestion(question)) {
    return generateUnsafeMedicalAnswer()
  }

  const topResult = recallTopResult(data)

  const sourceDetails = [
    `Source: ${data.source_name}`,
    `Retrieved: ${formatTimestamp(data.retrieval_timestamp)}`,
    `Audit ID: ${data.audit.audit_id}`,
    `Records matched: ${data.count}`,
  ]

  if (!topResult) {
    return {
      title: 'No matching recall records were returned',
      summary:
        'DAV AI did not find matching public FDA recall records for this search. That does not prove the product is safe or unsafe.',
      bullets: [
        'Try searching by brand name, product name, generic name, ingredient, or manufacturer.',
        'Check official FDA sources directly if this is time-sensitive.',
        'Use DAV AI as public-data review support, not as a safety guarantee.',
      ],
      sourceDetails,
      limitation: data.medical_disclaimer,
    }
  }

  if (prompt === 'verify') {
    return {
      title: 'What to verify',
      summary:
        'Compare the public recall result against the exact product or package you are reviewing.',
      bullets: [
        `Product description: ${topResult.product_description ?? 'Unknown'}`,
        `Recalling firm: ${topResult.recalling_firm ?? 'Unknown'}`,
        `Recall number: ${topResult.recall_number ?? 'Unknown'}`,
        `Recall date: ${formatDate(topResult.recall_initiation_date)}`,
        `FDA class/status: ${topResult.classification ?? 'Unknown'} / ${topResult.status ?? 'Unknown'}`,
        `Distribution: ${topResult.distribution_pattern ?? 'Unknown'}`,
        `Reason: ${topResult.reason_for_recall ?? 'No reason provided'}`,
      ],
      sourceDetails,
      limitation: data.medical_disclaimer,
    }
  }

  if (prompt === 'score') {
    return {
      title: 'What the review signal means',
      summary:
        'DAV AI uses a transparent rule-based score to highlight recall records that may deserve closer review. It is not a personal safety rating.',
      bullets: [
        `Highest visible signal: ${topResult.risk_score.label} (${topResult.risk_score.score}/100).`,
        `FDA class contribution: ${topResult.risk_score.components.classification_score}.`,
        `Status contribution: ${topResult.risk_score.components.status_score}.`,
        `Recency contribution: ${topResult.risk_score.components.recency_score}.`,
        `Scope contribution: ${topResult.risk_score.components.scope_score}.`,
        `Score version: ${topResult.risk_score.score_version}.`,
      ],
      sourceDetails,
      limitation: data.medical_disclaimer,
    }
  }

  if (prompt === 'source') {
    return {
      title: 'Where this data came from',
      summary:
        'This answer is based on the public FDA/openFDA recall search result currently shown in DAV AI.',
      bullets: [
        `Source name: ${data.source_name}.`,
        `Endpoint: ${data.endpoint}.`,
        `Retrieval timestamp: ${formatTimestamp(data.retrieval_timestamp)}.`,
        `Audit ID: ${data.audit.audit_id}.`,
        `Transform version: ${data.audit.transform_version}.`,
      ],
      sourceDetails,
      limitation: data.medical_disclaimer,
    }
  }

  return {
    title: 'Plain-English explanation',
    summary:
      'DAV AI found public FDA recall records that may match your search. Use the result as a review signal and compare it carefully with the official source and product details.',
    bullets: [
      `Top matched product: ${topResult.product_description ?? 'Unknown product'}.`,
      `Reason listed: ${topResult.reason_for_recall ?? 'No reason provided'}.`,
      `FDA class/status: ${topResult.classification ?? 'Unknown'} / ${topResult.status ?? 'Unknown'}.`,
      'A match may apply only to specific lots, packages, firms, dates, or distribution areas.',
      'No answer here proves whether a specific product is safe or unsafe for a specific person.',
    ],
    sourceDetails,
    limitation: data.medical_disclaimer,
  }
}

export function generateDrugEventAssistantAnswer(
  data: DrugEventSearchResponse,
  prompt: AskDavAIPrompt,
  question = ''
): AskDavAIAnswer {
  if (question && isUnsafeMedicalQuestion(question)) {
    return generateUnsafeMedicalAnswer()
  }

  const topReaction = data.top_reactions[0]
  const sourceDetails = [
    `Source: ${data.source_name}`,
    `Retrieved: ${formatTimestamp(data.retrieval_timestamp)}`,
    `Audit ID: ${data.audit.audit_id}`,
    `Records reviewed: ${data.count}`,
  ]

  if (prompt === 'top_reactions') {
    return {
      title: 'Top reported reactions',
      summary:
        'These are public FAERS reporting patterns only. They do not prove that the drug caused a reaction.',
      bullets:
        data.top_reactions.length > 0
          ? data.top_reactions
              .slice(0, 5)
              .map((item) => `${item.reaction}: ${item.count} public report mention(s).`)
          : ['No top reaction terms were returned for this search.'],
      sourceDetails,
      limitation: data.faers_disclaimer,
    }
  }

  if (prompt === 'faers_limits') {
    return {
      title: 'What FAERS does not prove',
      summary:
        'FAERS reports are useful for public safety-signal review, but they have major interpretation limits.',
      bullets: [
        'They do not prove causation.',
        'They are not incidence rates.',
        'They do not prove personal risk.',
        'Reports may be incomplete, duplicated, delayed, or influenced by reporting behavior.',
        'They should not be used as diagnosis, treatment guidance, or medication instructions.',
      ],
      sourceDetails,
      limitation: data.faers_disclaimer,
    }
  }

  if (prompt === 'score') {
    return {
      title: 'What the DrugSignal score means',
      summary:
        'The DrugSignal score is a review-priority signal based on returned public reports. It is not a clinical risk score.',
      bullets: [
        `Score: ${data.intelligence_score.score}/100 ${data.intelligence_score.label}.`,
        `Review priority: ${data.intelligence_score.review_priority}.`,
        `Data confidence: ${data.intelligence_score.data_confidence}.`,
        `Top reaction concentration: ${data.intelligence_score.top_reaction_concentration}%.`,
        `Score version: ${data.intelligence_score.score_version}.`,
      ],
      sourceDetails,
      limitation: data.faers_disclaimer,
    }
  }

  if (prompt === 'source') {
    return {
      title: 'Where this data came from',
      summary:
        'This answer is based on the public openFDA Drug Event result currently shown in DAV AI.',
      bullets: [
        `Source name: ${data.source_name}.`,
        `Endpoint: ${data.endpoint}.`,
        `Retrieval timestamp: ${formatTimestamp(data.retrieval_timestamp)}.`,
        `Audit ID: ${data.audit.audit_id}.`,
        `Transform version: ${data.audit.transform_version}.`,
        `Reaction classifier version: ${data.reaction_classifier_version}.`,
      ],
      sourceDetails,
      limitation: data.faers_disclaimer,
    }
  }

  return {
    title: 'Plain-English explanation',
    summary:
      'DAV AI reviewed public FAERS-style adverse-event reports for this search. These are reporting patterns only, not proof of causation.',
    bullets: [
      `${data.count} public report record(s) were reviewed.`,
      `DrugSignal score: ${data.intelligence_score.score}/100 ${data.intelligence_score.label}.`,
      topReaction
        ? `Top reported reaction term: ${topReaction.reaction} (${topReaction.count} mention(s)).`
        : 'No top reaction term was returned.',
      'Use this to guide public-data review, not medical decisions.',
    ],
    sourceDetails,
    limitation: data.faers_disclaimer,
  }
}
