import { apiClient } from './client'

export type SourceFreshnessStatus = 'fresh' | 'delayed' | 'unknown' | 'error'

export type SourceRecord = {
  source_id: string
  source_name: string
  endpoint: string
  module: string
  description: string
  update_cadence: string
  freshness_status: SourceFreshnessStatus
  freshness_label: string
  last_successful_retrieval_at: string | null
  last_attempted_retrieval_at: string | null
  last_record_count: number | null
  last_error_message: string | null
  freshness_reason: string
}

export type SourceRegistryResponse = {
  count: number
  sources: SourceRecord[]
}

export async function getSources() {
  const response = await apiClient.get<SourceRegistryResponse>(`/api/v1/sources`)
  return response.data
}
