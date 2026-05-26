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
  latest_period: string | null
  latest_value: number | null
  previous_period: string | null
  previous_value: number | null
  signal: RegionalHealthSignalSummary
  records: RegionalHealthPoint[]
  disclaimer: string
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
