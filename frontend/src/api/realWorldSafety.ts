import { apiClient } from './client'

export type RealWorldSafetySourceKind = 'structured_api' | 'public_notice'
export type RealWorldSafetySort = 'score' | 'latest'

export type RealWorldSafetyRecord = {
  source_name: string
  source_type: string
  source_url: string
  source_kind: RealWorldSafetySourceKind
  category: string | null
  product_name: string | null
  brand_name: string | null
  company_name: string | null
  title: string | null
  reason: string | null
  hazard_type: string | null
  remedy: string | null
  published_date: string | null
  recall_number: string | null
  affected_models: string[]
  affected_lots: string[]
  raw_payload_hash: string
  retrieved_at: string
  record_url: string | null
}

export type RealWorldSafetyCheckedSource = {
  source_id: string
  source_name: string
  source_type: string
  source_url: string
  source_kind: RealWorldSafetySourceKind
  upstream_status: string
  record_count: number
}

export type RealWorldSafetyFailedSource = {
  source_id: string
  source_name: string
  source_type: string
  source_url: string
  source_kind: RealWorldSafetySourceKind
  error_type: string
  reason: string
}

export type RealWorldSafetyQueryUnderstanding = {
  original_query: string
  normalized_query: string
  search_query: string
  corrections_applied: string[]
  expanded_terms: string[]
  expansion_search_terms_used: string[]
  detected_identifiers: Record<'vin' | 'ndc' | 'upc', string | null>
  query_type_hints: string[]
}

export type RealWorldSafetySourceRole =
  | 'recall_enforcement'
  | 'reference_identity'
  | 'label_reference'
  | 'signal_report'
  | 'other'

export type RealWorldSafetyIntelligenceSummary = {
  query_type: string
  recall_or_enforcement_found: boolean
  reference_or_label_found: boolean
  signal_report_found: boolean
  matched_sources_by_role: Record<RealWorldSafetySourceRole, string[]>
  checked_sources_by_role: Record<RealWorldSafetySourceRole, string[]>
  top_result_titles: string[]
  expansion_explanations: string[]
  plain_language_summary: string
  suggested_next_steps: string[]
  caveat: string
}

export type RealWorldSafetyAuditSummary = {
  audit_id: string
  source_id: string
  source_name: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
  source_snapshot_status: string | null
  source_pull_id: string | null
  source_payload_hash: string | null
}

export type RealWorldSafetySearchResponse = {
  query: string
  raw_query: string
  query_understanding: RealWorldSafetyQueryUnderstanding
  count: number
  limit: number
  retrieval_timestamp: string
  sources_checked: RealWorldSafetyCheckedSource[]
  sources_failed: RealWorldSafetyFailedSource[]
  records_per_source: Record<string, number>
  structured_api_matches: number
  public_notice_matches: number
  total_matches: number
  no_match_explanation: string | null
  safety_intelligence_summary: RealWorldSafetyIntelligenceSummary
  public_data_disclaimer: string
  limitations: string[]
  source_audits: RealWorldSafetyAuditSummary[]
  results: RealWorldSafetyRecord[]
}

export async function searchRealWorldSafety(
  query: string,
  limit = 10,
  sort: RealWorldSafetySort = 'score',
): Promise<RealWorldSafetySearchResponse> {
  const response = await apiClient.get<RealWorldSafetySearchResponse>(
    '/api/v1/real-world-safety/search',
    {
      params: {
        q: query,
        limit,
        sort,
      },
    },
  )

  return response.data
}
