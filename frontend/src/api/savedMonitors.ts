import { apiClient } from './client'

export type SavedMonitorModule = 'recallradar' | 'drugsignal'
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
  const response = await apiClient.post<SavedMonitor>(
    '/api/v1/saved-monitors',
    payload,
  )
  return response.data
}

export async function deleteSavedMonitor(monitorId: string): Promise<void> {
  await apiClient.delete(`/api/v1/saved-monitors/${monitorId}`)
}

export async function runSavedMonitor(monitorId: string): Promise<SavedMonitor> {
  const response = await apiClient.post<SavedMonitor>(
    `/api/v1/saved-monitors/${monitorId}/run`,
  )
  return response.data
}
