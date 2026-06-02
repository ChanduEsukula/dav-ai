import { describe, expect, it } from 'vitest'
import type { RecallSearchResponse } from '../api/recalls'
import type { DrugEventSearchResponse } from '../api/drugEvents'
import {
  generateDrugEventAssistantAnswer,
  generateRecallAssistantAnswer,
  isUnsafeMedicalQuestion,
} from './reviewAssistant'

const recallResponse: RecallSearchResponse = {
  query: 'eye drops',
  count: 1,
  limit: 1,
  source_name: 'openFDA Drug Enforcement API',
  endpoint: 'https://api.fda.gov/drug/enforcement.json',
  retrieval_timestamp: '2026-06-02T18:00:00Z',
  score_version: 'recall-risk-v0.1',
  medical_disclaimer: 'Public recall data only. Not medical advice.',
  audit: {
    audit_id: 'audit-recall-1',
    source_id: 'openfda_drug_enforcement',
    module: 'RecallRadar',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'recall-transform-v0.1',
  },
  results: [
    {
      recall_number: 'D-1234-2026',
      product_description: 'Example Eye Drops',
      reason_for_recall: 'Lack of assurance of sterility',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260601',
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Firm',
      risk_score: {
        score: 82,
        label: 'High',
        components: {
          classification_score: 30,
          status_score: 20,
          recency_score: 20,
          scope_score: 12,
        },
        score_version: 'recall-risk-v0.1',
      },
      source: {
        name: 'openFDA Drug Enforcement API',
        endpoint: 'https://api.fda.gov/drug/enforcement.json',
        retrieval_timestamp: '2026-06-02T18:00:00Z',
      },
    },
  ],
}

const drugResponse: DrugEventSearchResponse = {
  query: 'metformin',
  count: 2,
  limit: 2,
  source_name: 'openFDA Drug Event API',
  endpoint: 'https://api.fda.gov/drug/event.json',
  retrieval_timestamp: '2026-06-02T18:00:00Z',
  medical_disclaimer: 'Public-data safety intelligence only. Not medical advice.',
  faers_disclaimer: 'FAERS adverse-event reports do not prove causation.',
  audit: {
    audit_id: 'audit-drug-1',
    source_id: 'openfda_drug_event',
    module: 'DrugSignal',
    upstream_status: 'success',
    record_count: 2,
    transform_version: 'drug-event-transform-v0.1',
  },
  intelligence_score: {
    score: 67,
    label: 'High',
    data_confidence: 'Moderate',
    top_reaction_concentration: 25,
    review_priority: 'Review',
    score_version: 'drug-signal-intelligence-v0.1',
    limitations: ['FAERS reports are safety signals only and do not prove causation.'],
  },
  reaction_categories: [
    {
      category: 'Neurological',
      count: 2,
      reactions: ['Gait disturbance'],
    },
  ],
  reaction_classifier_version: 'reaction-classifier-v0.1',
  trend_snapshot: {
    label: 'Stable',
    current_record_count: 2,
    previous_record_count: 2,
    previous_audit_id: 'previous-audit',
    previous_created_at: '2026-06-02T17:00:00Z',
    explanation: 'Compared with the most recent stored DrugSignal audit event.',
    limitation: 'Trend is based only on stored searches in DAV AI.',
    trend_version: 'drug-signal-trend-v0.1',
  },
  top_reactions: [
    {
      reaction: 'Gait disturbance',
      count: 2,
    },
  ],
}

describe('reviewAssistant', () => {
  it('detects unsafe medical questions', () => {
    expect(isUnsafeMedicalQuestion('Should I stop taking this medicine?')).toBe(true)
    expect(isUnsafeMedicalQuestion('What should I verify on my bottle?')).toBe(false)
  })

  it('generates a recall verification checklist', () => {
    const answer = generateRecallAssistantAnswer(recallResponse, 'verify')

    expect(answer.title).toBe('What to verify')
    expect(answer.bullets.join(' ')).toContain('Example Eye Drops')
    expect(answer.bullets.join(' ')).toContain('Example Firm')
    expect(answer.sourceDetails.join(' ')).toContain('audit-recall-1')
  })

  it('generates a recall score explanation', () => {
    const answer = generateRecallAssistantAnswer(recallResponse, 'score')

    expect(answer.summary).toContain('rule-based score')
    expect(answer.bullets.join(' ')).toContain('82/100')
  })

  it('generates DrugSignal top reaction explanation', () => {
    const answer = generateDrugEventAssistantAnswer(drugResponse, 'top_reactions')

    expect(answer.bullets.join(' ')).toContain('Gait disturbance')
    expect(answer.limitation).toContain('do not prove causation')
  })

  it('generates FAERS limitation explanation', () => {
    const answer = generateDrugEventAssistantAnswer(drugResponse, 'faers_limits')

    expect(answer.bullets.join(' ')).toContain('They do not prove causation')
    expect(answer.bullets.join(' ')).toContain('They are not incidence rates')
  })

  it('refuses unsafe medical advice questions', () => {
    const answer = generateDrugEventAssistantAnswer(
      drugResponse,
      'plain_english',
      'Should I stop taking metformin?'
    )

    expect(answer.title).toContain('not give medical advice')
    expect(answer.summary).toContain('cannot provide medical advice')
  })
})
