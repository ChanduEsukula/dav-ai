import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

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
  medical_disclaimer: string
  audit: AuditSummary
  results: RecallResult[]
}

export async function searchRecalls(query: string, limit = 5) {
  const response = await axios.get<RecallSearchResponse>(
    `${API_BASE_URL}/api/v1/recalls/search`,
    {
      params: {
        q: query,
        limit,
      },
    }
  )

  return response.data
}