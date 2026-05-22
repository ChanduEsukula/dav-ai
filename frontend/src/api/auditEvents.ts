import { apiClient } from './client'

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

export type SourcePullProvenanceItem = {
  pull_id: string
  audit_id: string
  source_id: string | null
  source_name: string | null
  endpoint: string | null
  query: string | null
  query_params: Record<string, unknown> | null
  retrieval_timestamp: string | null
  upstream_status: string | null
  record_count: number | null
  payload_hash: string
  transform_version: string | null
  created_at: string | null
  snapshot_id: string | null
}

export type SourcePullProvenanceResponse = {
  status: string
  persistence_available: boolean
  item: SourcePullProvenanceItem | null
  message: string | null
}

export type AuditHistoryFilters = {
  module?: string
  upstreamStatus?: string
  searchText?: string
}

export async function getAuditEvents(
  limit = 50,
  filters: AuditHistoryFilters = {},
): Promise<AuditHistoryListResponse> {
  const response = await apiClient.get<AuditHistoryListResponse>(
    `/api/v1/audit-events`,
    {
      params: {
        limit,
        module: filters.module,
        upstream_status: filters.upstreamStatus,
        q: filters.searchText,
      },
    },
  )

  return response.data
}

export async function getAuditEventById(
  auditId: string,
): Promise<AuditHistoryDetailResponse> {
  const response = await apiClient.get<AuditHistoryDetailResponse>(
    `/api/v1/audit-events/${auditId}`,
  )

  return response.data
}

export async function getAuditEventSourcePull(
  auditId: string,
): Promise<SourcePullProvenanceResponse> {
  const response = await apiClient.get<SourcePullProvenanceResponse>(
    `/api/v1/audit-events/${auditId}/source-pull`,
  )

  return response.data
}
