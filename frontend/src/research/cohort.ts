import type { Candidate, PublicBriefing } from './contracts'

export type EvidenceStatus =
  | 'Available'
  | 'Partial'
  | 'Incomplete'
  | 'Unavailable'
  | 'Not evaluated'
  | 'Error'

export interface CohortItem {
  id: string
  product_ref?: string
  brand_names: string[]
  generic_name: string | null
  strength: string | null
  dosage_form: string | null
  routes: string[]
  product_ndcs: string[]
  package_ndcs: string[]
  active_ingredients: string[]
  label_status: EvidenceStatus
  recall_status: EvidenceStatus
  faers_status: EvidenceStatus
  coverage_summary: string
  last_research_status: EvidenceStatus
  last_briefing?: PublicBriefing | null
  added_at: string
}

export const MAX_COHORT_LIMIT = 50

export function createCohortItemFromCandidate(candidate: Candidate): CohortItem {
  const primaryNdc = candidate.product_ndcs[0] || candidate.product_ref
  return {
    id: primaryNdc,
    product_ref: candidate.product_ref,
    brand_names: candidate.brand_names,
    generic_name: candidate.generic_name,
    strength: candidate.strength,
    dosage_form: candidate.dosage_form,
    routes: candidate.routes,
    product_ndcs: candidate.product_ndcs,
    package_ndcs: candidate.package_ndcs,
    active_ingredients: candidate.active_ingredients,
    label_status: 'Not evaluated',
    recall_status: 'Not evaluated',
    faers_status: 'Not evaluated',
    coverage_summary: 'Frozen release snapshot (2020–2026)',
    last_research_status: 'Not evaluated',
    added_at: new Date().toISOString(),
  }
}

export function updateCohortItemWithBriefing(
  item: CohortItem,
  briefing: PublicBriefing
): CohortItem {
  let labelStatus: EvidenceStatus = 'Unavailable'
  let recallStatus: EvidenceStatus = 'Unavailable'
  let faersStatus: EvidenceStatus = 'Unavailable'

  briefing.sections.forEach((section) => {
    const s = section.status.toLowerCase()
    const mapStatus = (): EvidenceStatus => {
      if (s === 'complete' || s === 'completed') return 'Available'
      if (s === 'partial') return 'Partial'
      if (s === 'incomplete') return 'Incomplete'
      if (s === 'unavailable' || s === 'not_found') return 'Unavailable'
      if (s === 'error') return 'Error'
      return 'Not evaluated'
    }

    if (section.category === 'labels') labelStatus = mapStatus()
    if (section.category === 'recalls') recallStatus = mapStatus()
    if (section.category === 'faers') faersStatus = mapStatus()
  })

  let overallStatus: EvidenceStatus = 'Partial'
  const briefingState = briefing.status.toLowerCase()
  if (briefingState === 'complete' || briefingState === 'completed') overallStatus = 'Available'
  else if (briefingState === 'partial') overallStatus = 'Partial'
  else if (briefingState === 'stopped' || briefingState === 'error') overallStatus = 'Error'

  return {
    ...item,
    label_status: labelStatus,
    recall_status: recallStatus,
    faers_status: faersStatus,
    last_research_status: overallStatus,
    last_briefing: briefing,
  }
}
