import { expect, it, vi } from 'vitest'
import { apiClient } from './client'
import { getDrugLabels } from './drugCatalog'

vi.mock('./client', () => ({ apiClient: { get: vi.fn() } }))

it('rejects a label payload belonging to a different product', async () => {
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { drug_id: 'foreign', records: [] } })
  await expect(getDrugLabels('confirmed')).rejects.toThrow('binding mismatch')
})

it('admits only exact-product label records with a recognized stored selection', async () => {
  const admitted = { applicability_class: 'EXACT_PRODUCT', evidence_scope: 'PRODUCT', selection_status: 'SELECTED_STORED' }
  const earlier = { ...admitted, selection_status: 'EARLIER_STORED' }
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { drug_id: 'confirmed', records: [admitted, earlier,
    { ...admitted, applicability_class: 'INGREDIENT' }, { ...admitted, evidence_scope: 'INGREDIENT' },
    { ...admitted, selection_status: 'CANDIDATE' }] } })
  const result = await getDrugLabels('confirmed')
  expect(result.records).toEqual([admitted, earlier])
  expect(apiClient.get).toHaveBeenCalledWith('/api/drugs/confirmed/safety/labels', { signal: undefined })
})

it('treats missing label records as a failed payload rather than a no-warning finding', async () => {
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { drug_id: 'confirmed' } })
  await expect(getDrugLabels('confirmed')).rejects.toThrow('binding mismatch')
})

it('rejects unbound medication summaries rather than showing fabricated totals', async () => {
  const { getMedicationOverview } = await import('./drugCatalog')
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { query: 'foreign', products: [] } })
  await expect(getMedicationOverview('Xanax')).rejects.toThrow('scope could not be verified')
})

it('rejects recall links to products outside the returned discovery set', async () => {
  const { getMedicationOverview } = await import('./drugCatalog')
  const fixture = (await import('../test/medication-overview.fixture.json')).default
  const value = structuredClone(fixture)
  value.recalls.records[0].product_links[0].product_id = 'foreign'
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: value })
  await expect(getMedicationOverview('Xanax')).rejects.toThrow('inconsistent identities')
})

it('rejects malformed inventory responses instead of crashing the homepage', async () => {
  const { getDataInventory } = await import('./drugCatalog')
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { detail: 'Unexpected response' } })
  await expect(getDataInventory()).rejects.toThrow('inventory could not be verified')
})

it('requires all three primary inventory metrics and a valid coverage release', async () => {
  const { validateDataInventory } = await import('./drugCatalog')
  const fixture = (await import('../test/data-inventory.fixture.json')).default
  const value = structuredClone(fixture)
  value.metrics = value.metrics.filter(metric => metric.key !== 'recalls')
  expect(() => validateDataInventory(value as Parameters<typeof validateDataInventory>[0])).toThrow('inventory could not be verified')
})

it('validates the generated development metadata against the audited release facts', async () => {
  const { validateDataInventory } = await import('./drugCatalog')
  const generated = (await import('../generated/dev-inventory.json')).default
  const audited = (await import('../test/data-inventory.fixture.json')).default
  const value = validateDataInventory(generated as unknown as Parameters<typeof validateDataInventory>[0])
  expect(value.metrics).toEqual(audited.metrics)
  expect(value.release.release_id).toBe(audited.release.release_id)
  expect(JSON.stringify(generated)).not.toMatch(/\/Users\/|pharma_recovery|pairing|token/)
})
