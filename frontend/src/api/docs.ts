import { apiClient } from './client'

export type StaticDocsSearchResult = {
  title: string
  source_path: string
  section_heading: string | null
  snippet: string
  matched_terms: string[]
  line_start: number
  line_end: number
}

export type StaticDocsSearchResponse = {
  query: string
  count: number
  results: StaticDocsSearchResult[]
  limitations: string[]
}

export async function searchDocs(query: string, maxResults = 8) {
  const response = await apiClient.get<StaticDocsSearchResponse>(
    '/api/v1/docs/search',
    {
      params: {
        q: query,
        max_results: maxResults,
      },
    },
  )

  return response.data
}
