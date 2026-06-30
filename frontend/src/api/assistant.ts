import { apiClient } from './client'
import type { DrugEventSearchResponse } from './drugEvents'
import type { RecallSearchResponse } from './recalls'
import type { EverydaySafetySearchResponse } from './everydaySafety'
import type { CosmeticEventSearchResponse } from './cosmeticEvents'
import type { RealWorldSafetySearchResponse } from './realWorldSafety'

export type AssistantModule = 'recall' | 'drug_event' | 'food' | 'cosmetic' | 'public_safety'

export type AssistantSourceCitation = {
  label: string
  value: string
}

export type AssistantModelInfo = {
  provider: string
  model: string
}

export type AssistantSafetyInfo = {
  policy_version: string
  output_checked: boolean
}

export type AssistantRecallContext = {
  top_results: {
    recall_number: string | null
    product_description: string | null
    reason_for_recall: string | null
    classification: string | null
    status: string | null
    recall_initiation_date: string | null
    distribution_pattern: string | null
    recalling_firm: string | null
    risk_score_label: string
    risk_score_value: number
  }[]
}

export type AssistantDrugEventContext = {
  intelligence_score: {
    score: number
    label: string
    review_priority: string
    data_confidence: string
  }
  top_reactions: {
    reaction: string
    count: number
  }[]
  reaction_categories: {
    category: string
    count: number
    reactions: string[]
  }[]
  faers_disclaimer: string
}

export type AssistantFoodContext = {
  top_results: {
    recall_number: string | null
    product_description: string | null
    reason_for_recall: string | null
    classification: string | null
    status: string | null
    recall_initiation_date: string | null
    report_date: string | null
    distribution_pattern: string | null
    recalling_firm: string | null
    source_type: string | null
    risk_score_label: string
    risk_score_value: number
  }[]
}

export type AssistantCosmeticContext = {
  signal_score: {
    score: number
    label: string
    review_priority: string
    data_confidence: string
  }
  top_reactions: {
    reaction: string
    count: number
  }[]
  records: {
    report_number: string | null
    report_date: string | null
    serious: string | null
    products: string[]
    reactions: string[]
    outcomes: string[]
  }[]
  cosmetic_disclaimer: string
}

export type AssistantPublicSafetyContext = {
  summary: {
    query_type: string
    recall_or_enforcement_found: boolean
    reference_or_label_found: boolean
    signal_report_found: boolean
    plain_language_summary: string
    suggested_next_steps: string[]
    caveat: string
  }
  identifier_check: {
    user_message: string
    detected: {
      type: string
      label: string
      value: string | null
      source: string
      reason: string
    }[]
    to_verify: {
      type: string
      label: string
      value: string | null
      source: string
      reason: string
    }[]
  }
  sources_checked: {
    source_id: string
    source_name: string
    source_type: string
    source_kind: string
    upstream_status: string
    record_count: number
  }[]
  sources_failed: {
    source_id: string
    source_name: string
    reason: string
  }[]
  top_records: {
    title: string | null
    product_name: string | null
    brand_name: string | null
    company_name: string | null
    source_name: string
    source_type: string
    source_kind: string
    category: string | null
    reason: string | null
    hazard_type: string | null
    remedy: string | null
    published_date: string | null
    recall_number: string | null
    affected_models: string[]
    affected_lots: string[]
    record_url: string | null
    extraction_confidence: string | null
    source_text_excerpt: string | null
  }[]
}

export type AssistantPageContext = {
  query: string
  count: number
  source_name: string
  endpoint: string
  retrieval_timestamp: string
  audit_id: string
  limitations: string[]
  recall?: AssistantRecallContext
  drug_event?: AssistantDrugEventContext
  food?: AssistantFoodContext
  cosmetic?: AssistantCosmeticContext
  public_safety?: AssistantPublicSafetyContext
}

export type AssistantChatContext = {
  module: AssistantModule
  page_context: AssistantPageContext
}

export type AssistantChatRequest = AssistantChatContext & {
  question: string
}

export type AssistantChatResponse = {
  answer: string
  bullets: string[]
  refused: boolean
  refusal_reason: string | null
  source_citations: AssistantSourceCitation[]
  limitations: string[]
  model_info: AssistantModelInfo
  safety: AssistantSafetyInfo
}

export function buildRecallAssistantContext(data: RecallSearchResponse): AssistantChatContext {
  return {
    module: 'recall',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [data.medical_disclaimer],
      recall: {
        top_results: data.results.slice(0, 5).map((result) => ({
          recall_number: result.recall_number,
          product_description: result.product_description,
          reason_for_recall: result.reason_for_recall,
          classification: result.classification,
          status: result.status,
          recall_initiation_date: result.recall_initiation_date,
          distribution_pattern: result.distribution_pattern,
          recalling_firm: result.recalling_firm,
          risk_score_label: result.risk_score.label,
          risk_score_value: result.risk_score.score,
        })),
      },
    },
  }
}

export function buildFoodAssistantContext(data: EverydaySafetySearchResponse): AssistantChatContext {
  return {
    module: 'food',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [...data.limitations, data.public_data_disclaimer],
      food: {
        top_results: data.results.slice(0, 5).map((result) => ({
          recall_number: result.recall_number,
          product_description: result.product_description,
          reason_for_recall: result.reason_for_recall,
          classification: result.classification,
          status: result.status,
          recall_initiation_date: result.recall_initiation_date,
          report_date: result.report_date,
          distribution_pattern: result.distribution_pattern,
          recalling_firm: result.recalling_firm,
          source_type: result.source_type,
          risk_score_label: result.risk_score.label,
          risk_score_value: result.risk_score.score,
        })),
      },
    },
  }
}

function cosmeticProductLabel(product: CosmeticEventSearchResponse['records'][number]['products'][number]) {
  return (
    product.brand_name ||
    product.name_brand ||
    product.industry_name ||
    'Unnamed cosmetic product'
  )
}

export function buildCosmeticAssistantContext(data: CosmeticEventSearchResponse): AssistantChatContext {
  return {
    module: 'cosmetic',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [data.medical_disclaimer, data.cosmetic_disclaimer],
      cosmetic: {
        signal_score: {
          score: data.signal_score.score,
          label: data.signal_score.label,
          review_priority: data.signal_score.review_priority,
          data_confidence: data.signal_score.data_confidence,
        },
        top_reactions: data.top_reactions.slice(0, 5).map((reaction) => ({
          reaction: reaction.reaction,
          count: reaction.count,
        })),
        records: data.records.slice(0, 5).map((record) => ({
          report_number: record.report_number,
          report_date: record.report_date,
          serious: record.serious,
          products: record.products.slice(0, 10).map(cosmeticProductLabel),
          reactions: record.reactions.slice(0, 10),
          outcomes: record.outcomes.slice(0, 10),
        })),
        cosmetic_disclaimer: data.cosmetic_disclaimer,
      },
    },
  }
}

export function buildDrugEventAssistantContext(data: DrugEventSearchResponse): AssistantChatContext {
  return {
    module: 'drug_event',
    page_context: {
      query: data.query,
      count: data.count,
      source_name: data.source_name,
      endpoint: data.endpoint,
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: data.audit.audit_id,
      limitations: [data.medical_disclaimer, data.faers_disclaimer],
      drug_event: {
        intelligence_score: {
          score: data.intelligence_score.score,
          label: data.intelligence_score.label,
          review_priority: data.intelligence_score.review_priority,
          data_confidence: data.intelligence_score.data_confidence,
        },
        top_reactions: data.top_reactions.slice(0, 5).map((reaction) => ({
          reaction: reaction.reaction,
          count: reaction.count,
        })),
        reaction_categories: data.reaction_categories.slice(0, 5).map((category) => ({
          category: category.category,
          count: category.count,
          reactions: category.reactions.slice(0, 10),
        })),
        faers_disclaimer: data.faers_disclaimer,
      },
    },
  }
}

export function buildPublicSafetyAssistantContext(
  data: RealWorldSafetySearchResponse,
): AssistantChatContext {
  const firstAudit = data.source_audits[0]

  return {
    module: 'public_safety',
    page_context: {
      query: data.query,
      count: data.total_matches,
      source_name: 'DavAI Public Safety Search',
      endpoint: '/api/v1/real-world-safety/search',
      retrieval_timestamp: data.retrieval_timestamp,
      audit_id: firstAudit?.audit_id ?? 'not recorded',
      limitations: [...data.limitations, data.public_data_disclaimer].filter(Boolean).slice(0, 8),
      public_safety: {
        summary: {
          query_type: data.safety_intelligence_summary.query_type,
          recall_or_enforcement_found:
            data.safety_intelligence_summary.recall_or_enforcement_found,
          reference_or_label_found:
            data.safety_intelligence_summary.reference_or_label_found,
          signal_report_found: data.safety_intelligence_summary.signal_report_found,
          plain_language_summary:
            data.safety_intelligence_summary.plain_language_summary,
          suggested_next_steps:
            data.safety_intelligence_summary.suggested_next_steps.slice(0, 6),
          caveat: data.safety_intelligence_summary.caveat,
        },
        identifier_check: {
          user_message: data.identifier_check.user_message,
          detected: data.identifier_check.detected.slice(0, 8).map((item) => ({
            type: item.type,
            label: item.label,
            value: item.value,
            source: item.source,
            reason: item.reason,
          })),
          to_verify: data.identifier_check.to_verify.slice(0, 8).map((item) => ({
            type: item.type,
            label: item.label,
            value: item.value,
            source: item.source,
            reason: item.reason,
          })),
        },
        sources_checked: data.sources_checked.slice(0, 12).map((source) => ({
          source_id: source.source_id,
          source_name: source.source_name,
          source_type: source.source_type,
          source_kind: source.source_kind,
          upstream_status: source.upstream_status,
          record_count: source.record_count,
        })),
        sources_failed: data.sources_failed.slice(0, 8).map((source) => ({
          source_id: source.source_id,
          source_name: source.source_name,
          reason: source.reason,
        })),
        top_records: data.results.slice(0, 8).map((record) => ({
          title: record.title,
          product_name: record.product_name,
          brand_name: record.brand_name,
          company_name: record.company_name,
          source_name: record.source_name,
          source_type: record.source_type,
          source_kind: record.source_kind,
          category: record.category,
          reason: record.reason,
          hazard_type: record.hazard_type,
          remedy: record.remedy,
          published_date: record.published_date,
          recall_number: record.recall_number,
          affected_models: record.affected_models.slice(0, 10),
          affected_lots: record.affected_lots.slice(0, 10),
          record_url: record.record_url,
          extraction_confidence: record.extraction_confidence ?? null,
          source_text_excerpt: record.source_text_excerpt ?? null,
        })),
      },
    },
  }
}


export async function askDavAI(request: AssistantChatRequest) {
  const response = await apiClient.post<AssistantChatResponse>('/api/v1/assistant/chat', request)
  return response.data
}
