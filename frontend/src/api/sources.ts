import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

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
  const response = await axios.get<SourceRegistryResponse>(`${API_BASE_URL}/api/v1/sources`)
  return response.data
}