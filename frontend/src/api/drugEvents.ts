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