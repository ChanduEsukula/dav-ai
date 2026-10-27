import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import StoredDrugCatalog from './StoredDrugCatalog'
import { getDrugEvidence, getDrugLabels, searchCatalog } from '../api/drugCatalog'
import type { DrugEvidence } from '../api/drugCatalog'
import { generateReport } from '../api/reports'
import fixture from '../test/evidence.json'

vi.mock('../api/drugCatalog', () => ({ searchCatalog: vi.fn(), getDrugEvidence: vi.fn(), getDrugLabels: vi.fn() }))
vi.mock('../api/reports', () => ({ generateReport: vi.fn() }))
const evidence = fixture as DrugEvidence

beforeEach(() => {
  vi.resetAllMocks()
  window.history.replaceState(null, '', '/')
  vi.mocked(searchCatalog).mockResolvedValue({ results: [evidence.drug], count: 1 })
  vi.mocked(getDrugEvidence).mockResolvedValue(evidence)
  vi.mocked(getDrugLabels).mockResolvedValue({ drug_id: evidence.drug.id, records: [], latest_records: [], coverage: evidence.recalls.coverage })
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }
})

async function select() {
  fireEvent.change(screen.getByLabelText('Brand, generic name, active ingredient or NDC'), { target: { value: 'Ozempic' } })
  fireEvent.click(screen.getByRole('button', { name: 'Search drugs' }))
  fireEvent.click(await screen.findByRole('button', { name: /^Select .*NDC/i }))
  return screen.findByRole('button', { name: 'Generate PDF Report' })
}

describe('pharmaceutical explorer', () => {
  it('searches, selects exact identity and separates product recall from ingredient AE evidence', async () => {
    render(<StoredDrugCatalog />)
    await select()
    expect(searchCatalog).toHaveBeenCalledWith('Ozempic', 0, expect.any(AbortSignal))
    expect(screen.getByRole('heading', { name: 'Recall history' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Reported adverse events' })).toBeInTheDocument()
    expect(screen.getByText(/Manufacturer not independently verified/)).toBeInTheDocument()
    expect(screen.getAllByText(/never been recalled/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/ingredient-report associations/).length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: 'Expand Reported adverse events' }))
    fireEvent.click(screen.getByText('Monthly reporting trends'))
    expect(screen.getByText(evidence.adverse_events.records[0].monthly[0].period.slice(0, 7))).toBeInTheDocument()
  })

  it('downloads a PDF through POST and clears personal fields', async () => {
    vi.mocked(generateReport).mockResolvedValue(new Blob(['%PDF-test'], { type: 'application/pdf' }))
    URL.createObjectURL = vi.fn(() => 'blob:report')
    URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    render(<StoredDrugCatalog />)
    fireEvent.click(await select())
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Name (required)'), { target: { value: 'Test Reader' } })
    fireEvent.change(within(dialog).getByLabelText('Age (optional)'), { target: { value: '42' } })
    expect(within(dialog).getByLabelText('Selected drug')).toHaveAttribute('readonly')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Generate and download' }))
    await screen.findByText('Your PDF download is ready.')
    expect(generateReport).toHaveBeenCalledWith(evidence.drug.id, 'Test Reader', 42)
    expect(within(dialog).getByLabelText('Name (required)')).toHaveValue('')
    expect(window.location.search).not.toContain('Test')
  })

  it('shows recoverable errors and empty search results', async () => {
    vi.mocked(searchCatalog).mockRejectedValueOnce(new Error('unavailable')).mockResolvedValueOnce({ results: [], count: 0 })
    render(<StoredDrugCatalog />)
    fireEvent.change(screen.getByLabelText('Brand, generic name, active ingredient or NDC'), { target: { value: 'absent' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search drugs' }))
    await screen.findByRole('alert')
    fireEvent.click(screen.getByRole('button', { name: 'Retry search' }))
    expect(await screen.findByText(/No matching products/)).toBeInTheDocument()
  })

  it('restores product evidence on refresh and clears it on browser back', async () => {
    window.history.replaceState(null, '', `/?q=Ozempic&drug=${encodeURIComponent(evidence.drug.id)}`)
    render(<StoredDrugCatalog />)
    await screen.findByRole('button', { name: 'Generate PDF Report' })
    window.history.replaceState(null, '', '/')
    fireEvent.popState(window)
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Recall history' })).not.toBeInTheDocument())
  })

  it('keeps missing analytics distinct from zero and supports report failures', async () => {
    const missing = structuredClone(evidence)
    missing.adverse_events.records[0].analytics = null
    vi.mocked(getDrugEvidence).mockResolvedValue(missing)
    vi.mocked(generateReport).mockRejectedValue(new Error('limit'))
    render(<StoredDrugCatalog />)
    fireEvent.click(await select())
    expect(screen.getAllByText(/Missing data is not a zero count/)[0]).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Name (required)'), { target: { value: 'Test Reader' } })
    fireEvent.click(screen.getByRole('button', { name: 'Generate and download' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('PDF could not be generated')
  })
})

it('groups source records without losing their vintages or inventing missing URLs', async () => {
  const duplicate = structuredClone(evidence)
  duplicate.release.sources = [
    { source_id: 'archive', source_name: 'openfda_ndc_directory', source_url: 'https://download.open.fda.gov/drug/ndc/archive.zip', export_date: '2026-09-26', observed_at: '2026-09-26T15:05:08Z' },
    { source_id: 'identity', source_name: 'openfda_ndc_directory', source_url: null, export_date: null, observed_at: '2026-09-26T15:05:08Z' },
    { source_id: 'older', source_name: 'openfda_ndc_directory', source_url: 'https://api.fda.gov/drug/ndc.json', export_date: '2026-08-01', observed_at: null },
    { source_id: 'missing', source_name: 'other_source', source_url: null, export_date: null, observed_at: null },
  ]
  const original = structuredClone(duplicate)
  vi.mocked(getDrugEvidence).mockResolvedValue(duplicate)
  render(<StoredDrugCatalog />)
  await select()
  const sources = screen.getByRole('region', { name: 'Sources and data freshness' })
  expect(within(sources).getAllByText(/openfda_ndc_directory/)).toHaveLength(1)
  expect(within(sources).getByRole('link', { name: /Official FDA source/ })).toHaveAttribute('href', duplicate.release.sources[0].source_url)
  fireEvent.click(within(sources).getByText('Stored provenance records (3)'))
  expect(within(sources).getByText(/Exported: 2026-08-01/)).toBeInTheDocument()
  expect(within(sources).getAllByRole('link', { name: /Stored FDA reference/ }).map(link => link.getAttribute('href'))).toEqual([duplicate.release.sources[0].source_url, duplicate.release.sources[2].source_url])
  expect(within(sources).getByText('No URL stored for this provenance record.')).toBeInTheDocument()
  expect(within(sources).getByText('Official source link unavailable')).toBeInTheDocument()
  expect(duplicate).toEqual(original)
})

it('prefers a verified FDA reference without making unsafe source URLs clickable', async () => {
  const sources = structuredClone(evidence)
  const row = { source_id: 'unsafe', source_name: 'example', source_url: 'https://api.fda.gov.evil.example/fake', export_date: null, observed_at: null }
  sources.release.sources = [row, { ...row, source_id: 'safe', source_url: 'https://api.fda.gov/drug/ndc.json' }]
  vi.mocked(getDrugEvidence).mockResolvedValue(sources)
  render(<StoredDrugCatalog />)
  await select()
  const region = screen.getByRole('region', { name: 'Sources and data freshness' })
  expect(within(region).getByRole('link', { name: /Official FDA source/ })).toHaveAttribute('href', sources.release.sources[1].source_url)
  fireEvent.click(within(region).getByText('Stored provenance records (2)'))
  expect(within(region).getByText('Official source link unavailable')).toBeInTheDocument()
  expect(region.querySelector(`a[href="${row.source_url}"]`)).toBeNull()
})
