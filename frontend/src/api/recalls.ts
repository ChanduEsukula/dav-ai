import { apiClient } from './client'

export type RecallSort = 'score' | 'latest'

export type AuditSummary = {
  audit_id: string
  source_id: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
}

export type RecallResult = {
  recall_number: string | null
  product_description: string | null
  reason_for_recall: string | null
  classification: string | null
  status: string | null
  recall_initiation_date: string | null
  distribution_pattern: string | null
  recalling_firm: string | null
  risk_score: {
    score: number
    label: string
    components: {
      classification_score: number
      status_score: number
      recency_score: number
      scope_score: number
    }
    score_version: string
  }
  source: {
    name: string
    endpoint: string
    retrieval_timestamp: string
  }
}

export type RecallSearchResponse = {
  query: string
  count: number
  limit: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  score_version: string
  sort?: RecallSort
  medical_disclaimer: string
  audit: AuditSummary
  results: RecallResult[]
}

export async function searchRecalls(query: string, limit = 5, sort: RecallSort = 'score') {
  const response = await apiClient.get<RecallSearchResponse>(
    `/api/v1/recalls/search`,
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