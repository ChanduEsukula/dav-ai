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

const livePublicApiSourceIds = new Set([
  'openfda_drug_enforcement',
  'openfda_drug_event',
  'rxnorm_rxnav_api',
  'dailymed_spl_api',
  'openfda_drug_label',
  'openfda_ndc_directory',
  'openfda_device_enforcement',
  'openfda_device_event',
  'openfda_udi_directory',
  'openfda_cosmetic_event',
  'openfda_food_enforcement',
  'usda_fsis_recall',
  'nhtsa_vpic_vin_decoder_api',
  'nhtsa_recalls_api_datasets',
])

const curatedOfficialSnapshotSourceIds = new Set([
  'cpsc_recalls_api',
  'cdc_vaers',
  'cdc_foodborne_outbreaks',
  'foodradar_multi_source',
])

const livePublicPageSourceIds = new Set([
  'fda_recalls_market_withdrawals_safety_alerts',
  'fda_safety_communications',
])

const prototypeScaffoldSourceIds = new Set([
  'regional_health_pulse_demo',
])

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

  if (livePublicApiSourceIds.has(id)) {
    return 'live_public_api'
  }

  if (curatedOfficialSnapshotSourceIds.has(id)) {
    return 'curated_official_snapshot'
  }

  if (livePublicPageSourceIds.has(id)) {
    return 'live_public_page'
  }

  if (prototypeScaffoldSourceIds.has(id)) {
    return 'prototype_scaffold'
  }

  if (
    identity.includes('openfda') ||
    identity.includes('rxnorm') ||
    identity.includes('rxnav') ||
    identity.includes('dailymed') ||
    identity.includes('nhtsa_vpic') ||
    identity.includes('nhtsa_recall') ||
    identity.includes('usda_fsis') ||
    identity.includes('udi_directory')
  ) {
    return 'live_public_api'
  }

  if (
    identity.includes('cpsc_recalls') ||
    identity.includes('cdc_vaers') ||
    identity.includes('cdc_foodborne_outbreaks') ||
    identity.includes('foodradar_multi_source') ||
    name.includes('cpsc_recall')
  ) {
    return 'curated_official_snapshot'
  }

  if (
    identity.includes('fda_recalls_market_withdrawals_safety_alerts') ||
    identity.includes('fda_safety_communications') ||
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