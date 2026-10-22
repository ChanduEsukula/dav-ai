import { apiClient } from './client'

export type Provenance = {
  source: string
  source_id: string
  source_record_id: string
  source_url: string | null
  observed_at: string | null
}

export type RxCUIIdentity = {
  value: string
  concept_type: string | null
  is_unique_product: boolean
  has_conflict: boolean
}

export type CatalogDrug = {
  id: string
  product_id: string
  generic_name: string | null
  brand_names: string[]
  active_ingredients: string[]
  ingredient_ids: string[]
  strength: string | null
  dosage_form: string | null
  routes: string[]
  manufacturers: string[]
  product_ndcs: string[]
  package_ndcs: string[]
  rxcui: string | null
  rxcuis: RxCUIIdentity[]
  is_combination: boolean
  identity_partial: boolean
  formulation_id: string | null
  application_number: string | null
  product_type: string | null
  marketing_category: string | null
  consumer_classification: string
  provenance: Provenance
}

export type Coverage = {
  state: 'READY' | 'PARTIAL' | 'UNKNOWN' | 'UNAVAILABLE' | string
  reason_code: string
  scope: string
  as_of_date?: string | null
  source_date?: string | null
  measured_count?: number | null
  unresolved_count?: number | null
  stored_record_count: number
  bounded: boolean
  truncated: boolean | null
  empty_message: string
  limitations: string[]
}

export type IngredientCoverage = {
  ingredient_id?: string
  state: 'READY' | 'PARTIAL' | 'UNKNOWN' | 'UNAVAILABLE' | string
  reason_code: string
  scope: string
  as_of_date?: string | null
  source_date?: string | null
  measured_count?: number | null
  unresolved_count?: number | null
  limitations: string[]
}

export type LabelSectionState = {
  text: string | null
  field_present: boolean
  state: string
  reason_code: string
}

export type LabelRecord = {
  id: string
  label_set_id: string
  label_version: string | null
  selection_status: 'SELECTED_STORED' | 'EARLIER_STORED'
  effective_date: string | null
  applicability_class: string
  match_method: string | null
  matched_value: string | null
  evidence_scope: string
  boxed_warning: string | null
  warnings_and_precautions: string | null
  warnings: string | null
  contraindications: string | null
  adverse_reactions: string | null
  drug_interactions: string | null
  section_states: Record<string, LabelSectionState>
  source: string
  source_record_id: string
  source_url: string | null
}

export type RecallRecord = {
  id: string
  recall_number: string
  product_description: string
  reason_for_recall: string
  classification: string | null
  reported_status: string | null
  recalling_firm: string | null
  recall_initiation_date: string | null
  report_date: string | null
  distribution_pattern: string | null
  lot_information: string | null
  lot_scope: string
  applicability_class: string
  match_method: string | null
  matched_value: string | null
  source: string
  source_record_id: string
  source_url: string | null
}

export type AEReaction = {
  reaction: string
  co_report_activity: number
  active_months: number
  rank: number
}

export type AEAnalytics = {
  window_start: string
  window_end: string
  report_count: number
  unique_case_count: number
  serious_report_count: number
  serious_known_report_count: number
  death_report_count: number
  hospitalization_report_count: number
  disability_report_count: number
  life_threatening_report_count: number
  suspect_report_count: number
  concomitant_report_count: number
  interacting_report_count: number
  active_month_count: number
  reaction_term_count: number
  co_report_activity: number
  count_unit: string
  date_basis: string
  limitations: string[]
}

export type AEIngredientRecord = {
  ingredient_id: string
  ingredient_name: string
  scope: 'INGREDIENT' | string
  analytics: AEAnalytics | null
  monthly: { period: string; report_count: number; serious_report_count: number }[]
  top_reported_reactions: AEReaction[]
  coverage: IngredientCoverage
}

export type CommunicationRecord = {
  id: string
  ingredient_id: string
  ingredient_name: string
  title: string
  body_text: string
  published_date: string | null
  communication_type: string
  applicability_class: string
  scope_qualifiers: string
  source: string
  source_record_id: string
  source_url: string | null
}

export type DrugSafety = {
  drug_id: string
  labels: {
    records: LabelRecord[]
    latest_records: LabelRecord[]
    coverage: Coverage
  }
  recalls: {
    records: RecallRecord[]
    coverage: Coverage
  }
  adverse_events: {
    records: AEIngredientRecord[]
    coverage: Coverage
    summary: {
      scope: string
      ingredient_count: number
      ingredients_with_analytics: number
      ingredients_without_analytics: number
      product_report_total: null
      limitation: string
    }
  }
  communications: {
    records: CommunicationRecord[]
    coverage: Coverage & {
      ingredients?: IngredientCoverage[]
    }
  }
}

export type TimelineEvent = {
  source: string
  event_type: string
  date: string
  date_type: string
  title: string | null
  summary: string
  source_url: string | null
  record_id: string
}

export async function searchCatalog(
  q: string,
  offset = 0,
  signal?: AbortSignal,
) {
  return (
    await apiClient.get<{
      results: CatalogDrug[]
      count: number
    }>('/api/drugs/search', {
      params: { q, limit: 20, offset },
      signal,
    })
  ).data
}

export type Release = {
  release_id: string
  build_time_utc: string
  ndc_observation_date: string
  label_export_date: string
  window_start: string
  window_end: string
  sources: { source_id: string; source_name: string; source_url: string | null; export_date: string | null; observed_at: string | null }[]
}

export type DrugEvidence = {
  drug: CatalogDrug
  recalls: DrugSafety['recalls']
  adverse_events: DrugSafety['adverse_events']
  release: Release
  limitations: string[]
}

export async function getDrugEvidence(id: string, signal?: AbortSignal) {
  return (await apiClient.get<DrugEvidence>(`/api/drugs/${encodeURIComponent(id)}/evidence`, { signal })).data
}
