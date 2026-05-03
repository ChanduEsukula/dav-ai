export type BriefingRole = 'consumer' | 'pharmacy' | 'clinic' | 'public_health'

export type BriefingSource = 'recall' | 'drug_event'

export type SafetyBriefing = {
  role: BriefingRole
  source: BriefingSource
  title: string
  summary: string
  whatWasFound: string[]
  whatToVerify: string[]
  suggestedReviewChecklist: string[]
  limitations: string[]
  sourceDetails: {
    sourceName: string
    endpoint: string
    retrievalTimestamp: string
    auditId: string
    recordCount: number
  }
  disclaimer: string
}

export const briefingRoleLabels: Record<BriefingRole, string> = {
  consumer: 'Consumer',
  pharmacy: 'Pharmacy',
  clinic: 'Clinic',
  public_health: 'Public Health / Analyst',
}