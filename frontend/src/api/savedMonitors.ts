import { apiClient } from './client'

export type SavedMonitorModule =
  | 'recallradar'
  | 'drugsignal'
  | 'foodradar'
  | 'cosmeticsignal'
  | 'regional_health_pulse'

export type SavedMonitorStatus = 'not_checked' | 'checked' | 'error'

export interface SavedMonitor {
  id: string
  name: string
  query: string
  module: SavedMonitorModule
  created_at: string
  last_checked_at: string | null
  latest_audit_id: string | null
  latest_score: number | null
  previous_score: number | null
  latest_record_count: number | null
  previous_record_count: number | null
  status: SavedMonitorStatus
}

export type SavedMonitorRunStatus = 'success' | 'error'

export type PayloadChangeStatus = {
  label: 'first_seen' | 'unchanged' | 'changed' | 'unavailable' | 'unknown'
  previous_hash: string | null
  latest_hash: string | null
  reason: string
  safety_note: string
}

export interface SavedMonitorRun {
  run_id: string
  monitor_id: string
  module: SavedMonitorModule
  query: string
  status: SavedMonitorRunStatus
  record_count: number | null
  score: number | null
  score_label: string | null
  audit_id: string | null
  created_at: string
  error_message: string | null
  payload_change: PayloadChangeStatus | null
}

export type MonitorInsightLabel =
  | 'insufficient_history'
  | 'stable'
  | 'increased'
  | 'decreased'
  | 'notable_increase'
  | 'notable_decrease'
  | 'source_warning'

export interface MonitorInsight {
  monitor_id: string
  label: MonitorInsightLabel
  headline: string
  explanation: string
  latest_run_id: string | null
  previous_run_id: string | null
  latest_record_count: number | null
  previous_record_count: number | null
  record_count_delta: number | null
  percent_change: number | null
  latest_score: number | null
  previous_score: number | null
  score_delta: number | null
  confidence: string
  insight_version: string
  limitation: string
}

export interface CreateSavedMonitorPayload {
  name: string
  query: string
  module: SavedMonitorModule
}

export async function listSavedMonitors(): Promise<SavedMonitor[]> {
  const response = await apiClient.get<SavedMonitor[]>('/api/v1/saved-monitors')
  return response.data
}

export async function createSavedMonitor(
  payload: CreateSavedMonitorPayload,
): Promise<SavedMonitor> {
  const response = await apiClient.post<SavedMonitor>('/api/v1/saved-monitors', payload)
  return response.data
}

export async function deleteSavedMonitor(monitorId: string): Promise<void> {
  await apiClient.delete(`/api/v1/saved-monitors/${monitorId}`)
}

export async function runSavedMonitor(monitorId: string): Promise<SavedMonitor> {
  const response = await apiClient.post<SavedMonitor>(`/api/v1/saved-monitors/${monitorId}/run`)
  return response.data
}

export async function listSavedMonitorRuns(monitorId: string): Promise<SavedMonitorRun[]> {
  const response = await apiClient.get<SavedMonitorRun[]>(
    `/api/v1/saved-monitors/${monitorId}/runs`,
  )
  return response.data
}

export async function getSavedMonitorInsight(monitorId: string): Promise<MonitorInsight> {
  const response = await apiClient.get<MonitorInsight>(
    `/api/v1/saved-monitors/${monitorId}/insights`,
  )
  return response.data
}