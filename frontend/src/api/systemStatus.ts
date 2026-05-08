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

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  const response = await apiClient.get<SystemStatusResponse>('/api/v1/system/status')
  return response.data
}
