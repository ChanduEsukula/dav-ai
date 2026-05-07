import { apiClient } from './client'

export type SourceRecord = {
  source_id: string
  source_name: string
  endpoint: string
  module: string
  description: string
  update_cadence: string
}

export type SourceRegistryResponse = {
  count: number
  sources: SourceRecord[]
}

export async function getSources() {
  const response = await apiClient.get<SourceRegistryResponse>(`/api/v1/sources`)
  return response.data
}