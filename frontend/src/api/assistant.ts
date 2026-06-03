import { apiClient } from './client'
import type { DrugEventSearchResponse } from './drugEvents'
import type { RecallSearchResponse } from './recalls'

export type AssistantModule = 'recall' | 'drug_event'

export type AssistantSourceCitation = {
  label: string
  value: string
}

export type AssistantModelInfo = {
  provider: string
  model: string
}

export type AssistantSafetyInfo = {
  policy_version: string
  output_checked: boolean
}

export type AssistantRecallContext = {
  top_results: {
    recall_number: string | null
    product_description: string | null
    reason_for_recall: string | null
    classification: string | null
    status: string | null
    recall_initiation_date: string | null
    distribution_pattern: string | null
    recalling_firm: string | null
    risk_score_label: string
    risk_score_value: number
  }[]
}

export type AssistantDrugEventContext = {
  intelligence_score: {
    score: number
    label: string
    review_priority: string
    data_confidence: string
  }
  top_reactions: {
    reaction: string
    count: number
  }[]
  reaction_categories: {
    category: string
    count: number
    reactions: string[]
  }[]
  faers_disclaimer: string
}

export type AssistantPageContext = {
  query: string
  count: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  audit_id: string
  limitations: string[]
  recall?: AssistantRecallContext
  drug_event?: AssistantDrugEventContext
}

export type AssistantChatContext = {
  module: AssistantModule
  page_context: AssistantPageContext
}

export type AssistantChatRequest = AssistantChatContext & {
  question: string
}

export type AssistantChatResponse = {
  answer: string
  bullets: string[]
  refused: boolean
  refusal_reason: string | null
  source_citations: AssistantSourceCitation[]
  limitations: string[]
  model_info: AssistantModelInfo
  safety: AssistantSafetyInfo
}

export function buildRecallAssistantContext(data: RecallSearchResponse): AssistantChatContext {
  return {
    module: 'recall',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [data.medical_disclaimer],
      recall: {
        top_results: data.results.slice(0, 5).map((result) => ({
          recall_number: result.recall_number,
          product_description: result.product_description,
          reason_for_recall: result.reason_for_recall,
          classification: result.classification,
          status: result.status,
          recall_initiation_date: result.recall_initiation_date,
          distribution_pattern: result.distribution_pattern,
          recalling_firm: result.recalling_firm,
          risk_score_label: result.risk_score.label,
          risk_score_value: result.risk_score.score,
        })),
      },
    },
  }
}

export function buildDrugEventAssistantContext(data: DrugEventSearchResponse): AssistantChatContext {
  return {
    module: 'drug_event',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [data.medical_disclaimer, data.faers_disclaimer],
      drug_event: {
        intelligence_score: {
          score: data.intelligence_score.score,
          label: data.intelligence_score.label,
          review_priority: data.intelligence_score.review_priority,
          data_confidence: data.intelligence_score.data_confidence,
        },
        top_reactions: data.top_reactions.slice(0, 5).map((reaction) => ({
          reaction: reaction.reaction,
          count: reaction.count,
        })),
        reaction_categories: data.reaction_categories.slice(0, 5).map((category) => ({
          category: category.category,
          count: category.count,
          reactions: category.reactions.slice(0, 10),
        })),
        faers_disclaimer: data.faers_disclaimer,
      },
    },
  }
}

export async function askDavAI(request: AssistantChatRequest) {
  const response = await apiClient.post<AssistantChatResponse>('/api/v1/assistant/chat', request)
  return response.data
}
