import type { RecallResult } from '../api/recalls'

export function formatDate(value: string | null) {
  if (!value) return 'Unknown'

  if (/^\d{8}$/.test(value)) {
    const year = value.slice(0, 4)
    const month = value.slice(4, 6)
    const day = value.slice(6, 8)
    return `${month}/${day}/${year}`
  }

  return value
}

export function formatTimestamp(value: string) {
  try {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

export function riskExplanation(result: RecallResult) {
  const level = result.risk_score.label
  const classification = result.classification || 'an FDA recall classification'
  const status = result.status || 'unknown status'
  const scope = result.distribution_pattern?.toLowerCase().includes('nationwide')
    ? 'nationwide distribution'
    : 'documented distribution details'

  return `${level} signal based on ${classification}, ${status.toLowerCase()} status, ${scope}, and recall timing. Review the exact product, lot details, and FDA source before taking action.`
}