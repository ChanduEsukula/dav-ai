import { apiClient } from './client'

export type CosmeticProduct = {
  brand_name: string | null
  name_brand: string | null
  industry_code: string | null
  industry_name: string | null
}

export type CosmeticEventRecord = {
  report_number: string | null
  report_date: string | null
  serious: string | null
  outcomes: string[]
  reactions: string[]
  products: CosmeticProduct[]
}


export type CosmeticRecallNotice = {
  title: string | null
  product_name: string | null
  brand_name: string | null
  company_name: string | null
  category: string | null
  reason: string | null
  remedy?: string | null
  published_date: string | null
  record_url: string | null
  source_name: string
  source_kind?: 'structured_api' | 'public_notice' | 'normalized_public_notice'
  source_type?: string
  extraction_confidence?: string | null
}


export type CosmeticReaction = {
  reaction: string
  count: number
}

export type CosmeticSignalScore = {
  score: number
  label: string
  data_confidence: string
  top_reaction_concentration: number
  review_priority: string
  score_version: string
  limitations: string[]
}

export type CosmeticAudit = {
  audit_id: string
  source_id: string
  module: string
  upstream_status: string
  record_count: number
  transform_version: string
  source_snapshot_status: string | null
  source_pull_id: string | null
  source_payload_hash: string | null
}

export type CosmeticEventSearchResponse = {
  query: string
  raw_query?: string
  normalized_query?: string
  correction_applied?: boolean
  suggestion_message?: string | null
  count: number
  limit: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  medical_disclaimer: string
  cosmetic_disclaimer: string
  audit: CosmeticAudit
  signal_score: CosmeticSignalScore
  top_reactions: CosmeticReaction[]
  records: CosmeticEventRecord[]
  recall_count?: number
  recall_source_name?: string | null
  recall_source_status?: string | null
  recall_source_error?: string | null
  recall_notices?: CosmeticRecallNotice[]
}

export async function searchCosmeticEvents(
  query: string,
  limit = 10
): Promise<CosmeticEventSearchResponse> {
  const response = await apiClient.get<CosmeticEventSearchResponse>(
    '/api/v1/cosmetic-events/search',
    {
      params: {
        q: query,
        limit,
      },
    }
  )

  return response.data
}
