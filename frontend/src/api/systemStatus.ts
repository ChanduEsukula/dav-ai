import { apiClient } from './client'

export type SystemStatusResponse = {
  status: string
  app: string
  version: string
  database: {
    configured: boolean
    audit_readable: boolean
  }
  sources: {
    registered_count: number
    available: boolean
  }
  modules: string[]
}

export type DataQualityResponse = {
  status: string
  database_configured: boolean
  audit_readable: boolean
  source_registry_count: number
  recent_audit_count: number
  upstream_status_counts: {
    success: number
    empty: number
    error: number
  }
  latest_audit_event: {
    exists: boolean
    audit_id?: string | null
    module?: string | null
    query?: string | null
    upstream_status?: string | null
    record_count?: number | null
    created_at?: string | null
  }
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  const response = await apiClient.get<SystemStatusResponse>('/api/v1/system/status')
  return response.data
}

export async function getDataQuality(): Promise<DataQualityResponse> {
  const response = await apiClient.get<DataQualityResponse>('/api/v1/system/data-quality')
  return response.data
}
