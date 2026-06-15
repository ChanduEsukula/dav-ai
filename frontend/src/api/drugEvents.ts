import { apiClient } from './client'

export type AuditSummary = {
  audit_id: string
  source_id: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
}

export type DrugEventSort = 'reports' | 'alpha'

export type DrugEventReaction = {
  reaction: string
  count: number
}

export type DrugSignalIntelligenceScore = {
  score: number
  label: string
  data_confidence: string
  top_reaction_concentration: number
  review_priority: string
  score_version: string
  limitations: string[]
}

export type DrugReactionCategory = {
  category: string
  count: number
  reactions: string[]
}

export type DrugSignalTrendSnapshot = {
  label: string
  current_record_count: number
  previous_record_count: number | null
  previous_audit_id: string | null
  previous_created_at: string | null
  explanation: string
  limitation: string
  trend_version: string
}

export type DrugEventSearchResponse = {
  query: string
  raw_query?: string
  normalized_query?: string
  correction_applied?: boolean
  suggestion_message?: string | null
  count: number
  limit: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  medical_disclaimer: string
  faers_disclaimer: string
  audit: AuditSummary
  intelligence_score: DrugSignalIntelligenceScore
  reaction_categories: DrugReactionCategory[]
  reaction_classifier_version: string
  trend_snapshot: DrugSignalTrendSnapshot
  top_reactions: DrugEventReaction[]
}

export async function searchDrugEvents(query: string, limit = 10, sort: DrugEventSort = 'reports') {
  const response = await apiClient.get<DrugEventSearchResponse>(
    `/api/v1/drug-events/search`,
    {
      params: {
        q: query,
        limit,
        sort,
      },
    }
  )

  return response.data
}
