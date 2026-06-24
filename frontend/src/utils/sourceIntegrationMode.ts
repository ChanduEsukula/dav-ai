export type SourceIntegrationMode =
  | 'curated_official_snapshot'
  | 'live_public_api'
  | 'live_public_page'
  | 'prototype_scaffold'

export const sourceIntegrationModeLabels: Record<SourceIntegrationMode, string> = {
  curated_official_snapshot: 'Curated official snapshot',
  live_public_api: 'Live public API',
  live_public_page: 'Live public page',
  prototype_scaffold: 'Prototype scaffold',
}

type SourceIdentity = {
  sourceId?: string | null
  sourceName?: string | null
  sourceType?: string | null
}

function normalizeSourceValue(value: string | null | undefined) {
  return value?.trim().toLocaleLowerCase('en-US').replace(/[^a-z0-9]+/g, '_') ?? ''
}

export function getSourceIntegrationMode({
  sourceId,
  sourceName,
  sourceType,
}: SourceIdentity): SourceIntegrationMode | null {
  const id = normalizeSourceValue(sourceId)
  const name = normalizeSourceValue(sourceName)
  const type = normalizeSourceValue(sourceType)
  const identity = `${id} ${name} ${type}`

  if (
    identity.includes('usda_fsis') ||
    identity.includes('cpsc_recalls') ||
    name.includes('cpsc_recall')
  ) {
    return 'curated_official_snapshot'
  }

  if (identity.includes('nhtsa_vpic') || identity.includes('nhtsa_recall')) {
    return 'live_public_api'
  }

  if (
    identity.includes('fda_recalls_market_withdrawals_safety_alerts') ||
    id.includes('fda_public_notice') ||
    name.includes('fda_recalls_market_withdrawals_safety_alerts')
  ) {
    return 'live_public_page'
  }

  if (identity.includes('regional_health_pulse')) {
    return 'prototype_scaffold'
  }

  return null
}

