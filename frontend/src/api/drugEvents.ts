import { apiClient } from './client'

export type AuditSummary = {
  audit_id: string
  source_id: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
}

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

export type SemanticPreviewMatch = {
  record_id: string
  text: string
  similarity_score: number
  explanation: string
  source_name: string | null
}

export type SemanticPreview = {
  query_text: string
  matches: SemanticPreviewMatch[]
  limitations: string[]
  preview_version: string
  is_production_ml: boolean
}

export type DrugEventSearchResponse = {
  query: string
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
  semantic_preview?: SemanticPreview | null
  top_reactions: DrugEventReaction[]
}

export async function searchDrugEvents(query: string, limit = 10) {
  const response = await apiClient.get<DrugEventSearchResponse>(
    `/api/v1/drug-events/search`,
    {
      params: {
        q: query,
        limit,
      },
    }
  )

  return response.data
}