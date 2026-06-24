import {
  getSourceIntegrationMode,
  sourceIntegrationModeLabels,
} from './sourceIntegrationMode'

test.each([
  ['usda_fsis_recall', 'USDA FSIS Recall API', 'curated_official_snapshot'],
  ['cpsc_recalls_api', 'CPSC Recalls API', 'curated_official_snapshot'],
  ['nhtsa_recalls_api_datasets', 'NHTSA Recalls API / datasets', 'live_public_api'],
  [
    'fda_recalls_market_withdrawals_safety_alerts',
    'FDA Recalls, Market Withdrawals & Safety Alerts',
    'live_public_page',
  ],
  [
    'regional_health_pulse_demo',
    'Regional Health Pulse MVP scaffold',
    'prototype_scaffold',
  ],
] as const)('maps %s to its user-facing integration mode', (sourceId, sourceName, mode) => {
  expect(getSourceIntegrationMode({ sourceId, sourceName })).toBe(mode)
  expect(sourceIntegrationModeLabels[mode]).toBeTruthy()
})

test('does not infer a mode for unrelated public sources', () => {
  expect(
    getSourceIntegrationMode({
      sourceId: 'openfda_drug_enforcement',
      sourceName: 'openFDA Drug Enforcement API',
    }),
  ).toBeNull()
})

