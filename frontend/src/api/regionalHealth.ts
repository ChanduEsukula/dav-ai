import { apiClient } from './client'

export type RegionalHealthPoint = {
  period: string
  value: number
  label: string
}

export type RegionalHealthSignalSummary = {
  trend_label: string
  review_priority: string
  confidence: string
  change_percent: number | null
  signal_version: string
  limitations: string[]
}

export type RegionalHealthAuditSummary = {
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

export type RegionalHealthSourceFreshness = {
  freshness_status: string
  freshness_label: string
  source_update_cadence: string
  freshness_message: string
}

export type RegionalHealthSearchResponse = {
  module: string
  region: string
  category: string
  source_id: string
  source_name: string
  endpoint: string
  query: string
  retrieval_timestamp: string
  record_count: number
  source_freshness: RegionalHealthSourceFreshness
  latest_period: string | null
  latest_value: number | null
  previous_period: string | null
  previous_value: number | null
  signal: RegionalHealthSignalSummary
  records: RegionalHealthPoint[]
  disclaimer: string
  audit: RegionalHealthAuditSummary
}

export async function searchRegionalHealth(
  region: string,
  category: string,
): Promise<RegionalHealthSearchResponse> {
  const response = await apiClient.get<RegionalHealthSearchResponse>(
    '/api/v1/regional-health/search',
    {
      params: {
        region,
        category,
      },
    },
  )

  return response.data
}
