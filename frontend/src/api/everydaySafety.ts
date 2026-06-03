import { apiClient } from './client'

export type EverydaySafetySourceType =
  | 'FDA_FOOD_ENFORCEMENT'
  | 'USDA_FSIS_RECALL'

export type EverydaySafetyCategory = 'food_supplement'
export type EverydaySafetySort = 'score' | 'latest'

export type EverydaySafetyScoreComponents = {
  classification_score: number
  status_score: number
  recency_score: number
  scope_score: number
}

export type EverydaySafetyRiskScore = {
  score: number
  label: string
  components: EverydaySafetyScoreComponents
  score_version: string
}

export type EverydaySafetySource = {
  name: string
  endpoint: string
  retrieval_timestamp: string
}

export type EverydaySafetyCheckedSource = {
  source_id: string
  source_name: string
  source_type: EverydaySafetySourceType
  endpoint: string
  upstream_status: string
  record_count: number
}

export type EverydaySafetyRecord = {
  record_id: string | null
  recall_number: string | null
  product_description: string | null
  reason_for_recall: string | null
  classification: string | null
  status: string | null
  recall_initiation_date: string | null
  report_date: string | null
  distribution_pattern: string | null
  recalling_firm: string | null
  product_quantity: string | null
  code_info: string | null
  source_type: EverydaySafetySourceType
  search_strategy_used: string
  risk_score: EverydaySafetyRiskScore
  source: EverydaySafetySource
}

export type EverydaySafetyAudit = {
  audit_id: string
  source_id: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
  source_snapshot_status: string | null
  source_pull_id: string | null
  source_payload_hash: string | null
}

export type EverydaySafetySearchResponse = {
  query: string
  category: EverydaySafetyCategory
  category_label: string
  count: number
  limit: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  score_version: string
  search_strategy_used: string
  sources_checked: EverydaySafetyCheckedSource[]
  public_data_disclaimer: string
  limitations: string[]
  audit: EverydaySafetyAudit
  results: EverydaySafetyRecord[]
}

export async function searchEverydaySafety(
  query: string,
  limit = 5,
  category: EverydaySafetyCategory = 'food_supplement',
  sort: EverydaySafetySort = 'score'
): Promise<EverydaySafetySearchResponse> {
  const response = await apiClient.get<EverydaySafetySearchResponse>(
    '/api/v1/everyday-safety/search',
    {
      params: {
        category,
        q: query,
        limit,
        sort,
      },
    }
  )

  return response.data
}
