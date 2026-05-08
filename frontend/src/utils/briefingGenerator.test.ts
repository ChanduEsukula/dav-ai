import {
  generateDrugEventBriefing,
  generateRecallBriefing,
} from './briefingGenerator'
import type { RecallSearchResponse } from '../api/recalls'
import type { DrugEventSearchResponse } from '../api/drugEvents'

const recallResponse: RecallSearchResponse = {
  query: 'eye drops',
  count: 1,
  limit: 5,
  source_name: 'openFDA Drug Enforcement API',
  endpoint: 'https://api.fda.gov/drug/enforcement.json',
  retrieval_timestamp: '2026-05-03T12:00:00Z',
  score_version: 'recall-score-v1',
  medical_disclaimer:
    'MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.',
  audit: {
    audit_id: 'audit-123',
    source_id: 'openfda-drug-enforcement',
    module: 'RecallRadar',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'recall-transform-v1',
  },
  results: [
    {
      recall_number: 'D-1234-2026',
      product_description: 'Example Eye Drops',
      reason_for_recall: 'Potential microbial contamination',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260420',
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Pharma',
      risk_score: {
        score: 72,
        label: 'High',
        components: {
          classification_score: 30,
          status_score: 20,
          recency_score: 12,
          scope_score: 10,
        },
        score_version: 'recall-score-v1',
      },
      source: {
        name: 'openFDA Drug Enforcement API',
        endpoint: 'https://api.fda.gov/drug/enforcement.json',
        retrieval_timestamp: '2026-05-03T12:00:00Z',
      },
    },
  ],
}

const drugEventResponse: DrugEventSearchResponse = {
  query: 'metformin',
  count: 2,
  limit: 10,
  source_name: 'openFDA Drug Event API',
  endpoint: 'https://api.fda.gov/drug/event.json',
  retrieval_timestamp: '2026-05-03T12:00:00Z',
  medical_disclaimer:
    'MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.',
  faers_disclaimer:
    'FAERS reports are safety signals only and do not prove causation.',
  audit: {
    audit_id: 'drug-audit-123',
    source_id: 'openfda-drug-event',
    module: 'DrugSignal',
    upstream_status: 'success',
    record_count: 2,
    transform_version: 'drug-event-transform-v1',
  },
  intelligence_score: {
    score: 57,
    label: 'Moderate',
    data_confidence: 'Limited',
    top_reaction_concentration: 66.67,
    review_priority: 'Watch',
    score_version: 'drug-signal-intelligence-v0.1',
    limitations: [
      'FAERS reports are safety signals only and do not prove causation.',
      'Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.',
    ],
  },
  reaction_categories: [
    {
      category: 'Gastrointestinal',
      count: 12,
      reactions: ['NAUSEA'],
    },
    {
      category: 'Neurological',
      count: 6,
      reactions: ['HEADACHE'],
    },
  ],
  reaction_classifier_version: 'reaction-classifier-v0.1',
  trend_snapshot: {
    label: 'Increased',
    current_record_count: 2,
    previous_record_count: 1,
    previous_audit_id: 'previous-audit-123',
    previous_created_at: '2026-05-02T12:00:00Z',
    explanation: 'Compared with the most recent stored DrugSignal audit event for this query.',
    limitation: 'Trend is based only on stored public-data searches in MedTrek AI, not all FDA activity.',
    trend_version: 'drug-signal-trend-v0.1',
  },
  top_reactions: [
    {
      reaction: 'NAUSEA',
      count: 12,
    },
  ],
}

test('generates a consumer recall briefing with source and audit details', () => {
  const briefing = generateRecallBriefing(recallResponse, 'consumer')

  expect(briefing.role).toBe('consumer')
  expect(briefing.source).toBe('recall')
  expect(briefing.summary).toContain('eye drops')
  expect(briefing.whatWasFound.join(' ')).toContain('High')
  expect(briefing.whatWasFound.join(' ')).toContain('Example Eye Drops')
  expect(briefing.sourceDetails.sourceName).toBe('openFDA Drug Enforcement API')
  expect(briefing.sourceDetails.auditId).toBe('audit-123')
  expect(briefing.disclaimer).toContain('not medical advice')
})

test('generates a pharmacy recall briefing with inventory review language', () => {
  const briefing = generateRecallBriefing(recallResponse, 'pharmacy')

  expect(briefing.role).toBe('pharmacy')
  expect(briefing.suggestedReviewChecklist.join(' ')).toContain('inventory')
  expect(briefing.suggestedReviewChecklist.join(' ')).toContain('lot')
})

test('handles recall no-results safely', () => {
  const briefing = generateRecallBriefing(
    {
      ...recallResponse,
      count: 0,
      audit: {
        ...recallResponse.audit,
        record_count: 0,
      },
      results: [],
    },
    'consumer'
  )

  expect(briefing.whatWasFound.join(' ')).toContain('No FDA recall records')
  expect(briefing.limitations.join(' ')).toContain(
    'No-results output does not prove absence'
  )
})

test('generates a DrugSignal briefing without causation claims', () => {
  const briefing = generateDrugEventBriefing(drugEventResponse, 'clinic')
  const fullText = [
    briefing.summary,
    ...briefing.whatWasFound,
    ...briefing.whatToVerify,
    ...briefing.limitations,
  ].join(' ')

  expect(briefing.role).toBe('clinic')
  expect(briefing.source).toBe('drug_event')
  expect(fullText).toContain('NAUSEA')
  expect(fullText).toContain('DrugSignal Intelligence score: 57/100 Moderate')
  expect(fullText).toContain('Review priority: Watch')
  expect(fullText).toContain('Data confidence: Limited')
  expect(fullText).toContain('Top reaction concentration: 66.67%')
  expect(fullText).toContain('Leading reaction category: Gastrointestinal')
  expect(fullText).toContain('drug-signal-intelligence-v0.1')
  expect(fullText).toContain('reaction-classifier-v0.1')
  expect(fullText).toContain('rule-based')
  expect(fullText).toContain('not proof of causation')
  expect(fullText.toLowerCase()).not.toContain('caused by this drug')
  expect(briefing.sourceDetails.auditId).toBe('drug-audit-123')
})

test('handles DrugSignal no-results safely', () => {
  const briefing = generateDrugEventBriefing(
    {
      ...drugEventResponse,
      count: 0,
      audit: {
        ...drugEventResponse.audit,
        record_count: 0,
      },
      reaction_categories: [],
      trend_snapshot: {
        ...drugEventResponse.trend_snapshot,
        label: 'Insufficient history',
        current_record_count: 0,
        previous_record_count: null,
        previous_audit_id: null,
        previous_created_at: null,
        explanation: 'No previous stored DrugSignal audit event was available for this query.',
      },
      top_reactions: [],
    },
    'public_health'
  )

  expect(briefing.role).toBe('public_health')
  expect(briefing.whatWasFound.join(' ')).toContain('No FAERS drug-event records')
  expect(briefing.whatWasFound.join(' ')).toContain('does not prove')
  expect(briefing.whatWasFound.join(' ')).toContain('DrugSignal Intelligence score')
  expect(briefing.whatToVerify.join(' ')).toContain('drug-signal-intelligence-v0.1')
  expect(briefing.whatToVerify.join(' ')).toContain('reaction-classifier-v0.1')
})