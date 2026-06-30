import {
  getSourceIntegrationMode,
  sourceIntegrationModeLabels,
} from './sourceIntegrationMode'

test.each([
  ['openfda_drug_enforcement', 'openFDA Drug Enforcement API', 'live_public_api'],
  ['openfda_drug_event', 'openFDA Drug Event API', 'live_public_api'],
  ['rxnorm_rxnav_api', 'RxNorm/RxNav API', 'live_public_api'],
  ['dailymed_spl_api', 'DailyMed SPL API', 'live_public_api'],
  ['openfda_drug_label', 'openFDA Drug Label API', 'live_public_api'],
  ['openfda_ndc_directory', 'openFDA NDC Directory API', 'live_public_api'],
  ['openfda_device_enforcement', 'openFDA Device Enforcement API', 'live_public_api'],
  ['openfda_device_event', 'openFDA Device Event API', 'live_public_api'],
  ['openfda_udi_directory', 'openFDA UDI Directory API', 'live_public_api'],
  ['openfda_cosmetic_event', 'openFDA Cosmetic Event API', 'live_public_api'],
  ['openfda_food_enforcement', 'openFDA Food Enforcement API', 'live_public_api'],
  ['usda_fsis_recall', 'USDA FSIS Recall API', 'live_public_api'],
  ['nhtsa_vpic_vin_decoder_api', 'NHTSA vPIC VIN Decoder API', 'live_public_api'],
  ['nhtsa_recalls_api_datasets', 'NHTSA Recalls API / datasets', 'live_public_api'],
  ['cpsc_recalls_api', 'CPSC Recalls API', 'curated_official_snapshot'],
  ['cdc_vaers', 'CDC/VAERS public vaccine adverse-event reports', 'curated_official_snapshot'],
  ['cdc_foodborne_outbreaks', 'CDC/FDA Foodborne Outbreak Context', 'curated_official_snapshot'],
  ['foodradar_multi_source', 'FoodRadar Multi-Source Search', 'curated_official_snapshot'],
  [
    'fda_recalls_market_withdrawals_safety_alerts',
    'FDA Recalls, Market Withdrawals & Safety Alerts',
    'live_public_page',
  ],
  ['fda_safety_communications', 'FDA Safety Communications', 'live_public_page'],
  [
    'regional_health_pulse_demo',
    'Regional Health Pulse MVP scaffold',
    'prototype_scaffold',
  ],
] as const)('maps %s to its user-facing integration mode', (sourceId, sourceName, mode) => {
  expect(getSourceIntegrationMode({ sourceId, sourceName })).toBe(mode)
  expect(sourceIntegrationModeLabels[mode]).toBeTruthy()
})

test('falls back from source name and source type when source id is missing', () => {
  expect(
    getSourceIntegrationMode({
      sourceName: 'openFDA Drug Enforcement API',
      sourceType: 'live public API request',
    }),
  ).toBe('live_public_api')

  expect(
    getSourceIntegrationMode({
      sourceName: 'FDA Recalls, Market Withdrawals & Safety Alerts',
      sourceType: 'live public page ingestion',
    }),
  ).toBe('live_public_page')

  expect(
    getSourceIntegrationMode({
      sourceName: 'CPSC Recalls API',
      sourceType: 'local curated official snapshot',
    }),
  ).toBe('curated_official_snapshot')
})

test('does not infer a mode for unrelated public sources', () => {
  expect(
    getSourceIntegrationMode({
      sourceId: 'unknown_source',
      sourceName: 'Unknown public source',
    }),
  ).toBeNull()
})