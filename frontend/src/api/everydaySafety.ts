import { apiClient } from './client'

export type EverydaySafetySourceType =
  | 'FDA_FOOD_ENFORCEMENT'
  | 'USDA_FSIS_RECALL'
  | 'FDA_PUBLIC_NOTICE'
  | 'FDA_NORMALIZED_PUBLIC_NOTICE'

export type EverydaySafetySourceKind =
  | 'structured_api'
  | 'public_notice'
  | 'normalized_public_notice'

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
  source_kind?: EverydaySafetySourceKind
  source_type?: string
}

export type EverydaySafetyCheckedSource = {
  source_id: string
  source_name: string
  source_type: EverydaySafetySourceType
  source_kind?: EverydaySafetySourceKind
  record_type?: string
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
  source_kind?: EverydaySafetySourceKind
  source_record_type?: string
  title?: string | null
  product_name?: string | null
  brand_name?: string | null
  company_name?: string | null
  remedy?: string | null
  official_url?: string | null
  affected_models?: string[]
  affected_lots?: string[]
  extraction_confidence?: string | null
  source_text_excerpt?: string | null
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
  raw_query?: string
  normalized_query?: string
  correction_applied?: boolean
  suggestion_message?: string | null
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
