import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export type AuditHistoryItem = {
  audit_id: string
  module: string
  source_id: string
  source_name: string
  endpoint: string
  query: string
  query_params: Record<string, unknown>
  retrieval_timestamp: string
  upstream_status: string
  record_count: number
  transform_version: string
  score_version: string | null
  disclaimer_version: string | null
  error_message: string | null
  created_at: string
}

export type AuditHistoryListResponse = {
  status: string
  persistence_available: boolean
  count: number
  items: AuditHistoryItem[]
}

export type AuditHistoryDetailResponse = {
  status: string
  persistence_available: boolean
  item: AuditHistoryItem | null
  message: string | null
}

export async function getAuditEvents(limit = 50): Promise<AuditHistoryListResponse> {
  const response = await axios.get<AuditHistoryListResponse>(
    `${API_BASE_URL}/api/v1/audit-events`,
    {
      params: { limit },
    },
  )

  return response.data
}

export async function getAuditEventById(
  auditId: string,
): Promise<AuditHistoryDetailResponse> {
  const response = await axios.get<AuditHistoryDetailResponse>(
    `${API_BASE_URL}/api/v1/audit-events/${auditId}`,
  )

  return response.data
}