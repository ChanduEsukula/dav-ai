import { render, screen, waitFor, fireEvent, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import Workspace from './Workspace'
import { Briefing } from './Evidence'
import { researchApi } from './client'
import type { PublicBriefing } from './contracts'
import fixture from './briefing.fixture.json'

vi.mock('./client', () => ({ researchApi: { create: vi.fn(), search: vi.fn(), confirm: vi.fn(), run: vi.fn(), result: vi.fn(), cancel: vi.fn(), close: vi.fn() } }))
const product = { product_ref: 'p_owned', brand_names: ['Xanax'], generic_name: 'alprazolam', strength: '.25 mg/1', dosage_form: 'TABLET', routes: ['ORAL'], active_ingredients: ['alprazolam'], product_ndcs: ['0009-0029'], package_ndcs: ['0009-0029-01'] }
const briefing = { ...fixture, medication: { ...fixture.medication, ...product } } as PublicBriefing
beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(researchApi.create).mockResolvedValue({ session_id: 'opaque', capability: 'secret', expires_in: 600, models: [], model_runtime: 'unavailable' })
  vi.mocked(researchApi.search).mockResolvedValue({ state: 'confirmation_required', candidates: [product], results_may_be_incomplete: false })
  vi.mocked(researchApi.confirm).mockResolvedValue({ state: 'confirmed', medication: product })
  vi.mocked(researchApi.run).mockResolvedValue({ state: 'running', code: null, briefing: null })
  vi.mocked(researchApi.result).mockResolvedValue({ state: 'partial', briefing, code: null })
  vi.mocked(researchApi.close).mockResolvedValue({ state: 'closed', code: null, briefing: null })
})
async function connect() {
  const user = userEvent.setup()
  render(<Workspace />)
  await user.type(screen.getByLabelText('Local pairing capability'), 'local-pairing-secret')
  await user.click(screen.getByRole('button', { name: 'Create local session' }))
  await screen.findByLabelText('Brand, ingredient or NDC')
  return user
}
async function confirm() {
  const user = await connect()
  await user.type(screen.getByLabelText('Brand, ingredient or NDC'), 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  await user.click(await screen.findByRole('button', { name: /Xanax.*Product NDC/ }))
  await user.click(screen.getByRole('button', { name: 'Confirm selected product' }))
  await screen.findByText('Confirmed product')
  return user
}
it('requires explicit singleton selection/confirmation and sends explicit category scope once', async () => {
  const user = await connect()
  expect(screen.getByRole('button', { name: 'Research selected evidence' })).toBeDisabled()
  await user.type(screen.getByLabelText('Brand, ingredient or NDC'), 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(await screen.findByText('1 candidate · explicit confirmation required')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Confirm selected product' })).toBeDisabled()
  expect(researchApi.confirm).not.toHaveBeenCalled()
  await user.click(screen.getByRole('button', { name: /Xanax.*Product NDC/ }))
  await user.click(screen.getByRole('button', { name: 'Confirm selected product' }))
  await screen.findByText('Confirmed product')
  await user.click(screen.getByLabelText('Drug labeling'))
  await user.dblClick(screen.getByRole('button', { name: 'Research selected evidence' }))
  expect(researchApi.run).toHaveBeenCalledTimes(1)
  expect(vi.mocked(researchApi.run).mock.calls[0][2]).toEqual(['recalls', 'faers'])
  expect(await screen.findByRole('region', { name: 'Research briefing' })).toBeVisible()
  expect(screen.getByText('No admitted exact-product label is available in this frozen evidence release.')).toBeVisible()
  expect(screen.getByText(/They do not establish causation, incidence/)).toBeVisible()
  expect(screen.getByText(/Lot scope may be unknown or restricted/)).toBeVisible()
})
it('shows empty search and network errors without making a selection', async () => {
  vi.mocked(researchApi.search).mockResolvedValueOnce({ state: 'empty', candidates: [], results_may_be_incomplete: false }).mockRejectedValueOnce(new Error('api_unavailable'))
  const user = await connect()
  await user.type(screen.getByLabelText('Brand, ingredient or NDC'), 'missing')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(await screen.findByText(/No matching products/)).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('local API is unavailable')
})
it.each(['session_expired', 'session_forbidden', 'unknown_product_reference'])('handles %s and permits a fresh session', async code => {
  vi.mocked(researchApi.confirm).mockRejectedValueOnce(new Error(code))
  const user = await connect()
  await user.type(screen.getByLabelText('Brand, ingredient or NDC'), 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  await user.click(await screen.findByRole('button', { name: /Xanax.*Product NDC/ }))
  await user.click(screen.getByRole('button', { name: 'Confirm selected product' }))
  expect(await screen.findByRole('alert')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'New research session' }))
  expect(await screen.findByLabelText('Local pairing capability')).toBeVisible()
})
it('shows honest running state, supports cancellation and prevents repeated click dispatch', async () => {
  vi.mocked(researchApi.result).mockResolvedValue({ state: 'running', code: null, briefing: null })
  vi.mocked(researchApi.cancel).mockResolvedValue({ state: 'stopped', code: 'cancelled', briefing: null })
  await confirm()
  const run = screen.getByRole('button', { name: 'Research selected evidence' })
  fireEvent.click(run); fireEvent.click(run)
  await screen.findByText('Research is running locally')
  expect(researchApi.run).toHaveBeenCalledTimes(1)
  await userEvent.click(screen.getByRole('button', { name: 'Cancel and close session' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Research cancelled')
  expect(researchApi.cancel).toHaveBeenCalledTimes(1)
})
it('renders completed results and transparent deterministic routing', async () => {
  render(<Briefing value={{ ...briefing, status: 'completed' }} />)
  expect(screen.getByText('completed', { exact: true })).toBeVisible()
  await userEvent.click(screen.getByText('Research execution details'))
  expect(screen.getByText('Explicit deterministic execution · no model planning')).toBeVisible()
  expect(screen.getByText(/Backend selected: get_drug_label_evidence/)).toBeVisible()
  expect(screen.getAllByRole('link').every(link => link.getAttribute('href')?.startsWith('https://api.fda.gov/'))).toBe(true)
})
it('does not submit duplicate connection operations while the request is pending', async () => {
  let finish!: (value: Awaited<ReturnType<typeof researchApi.create>>) => void
  vi.mocked(researchApi.create).mockReturnValue(new Promise(resolve => { finish = resolve }))
  render(<Workspace />)
  fireEvent.change(screen.getByLabelText('Local pairing capability'), { target: { value: 'secret' } })
  const button = screen.getByRole('button', { name: 'Create local session' })
  fireEvent.click(button); fireEvent.click(button)
  expect(researchApi.create).toHaveBeenCalledTimes(1)
  finish({ session_id: 'opaque', capability: 'secret', expires_in: 600, models: [], model_runtime: 'unavailable' })
  await waitFor(() => expect(screen.getByRole('search')).toBeVisible())
})

it('renders full stored label text in accessible expandable sections', async () => {
  const { Labels } = await import('./Evidence')
  const { default: label } = await import('./label.fixture.json')
  const { default: userEvent } = await import('@testing-library/user-event')
  const longText = 'Stored exact-product warning. '.repeat(1000)
  const value = structuredClone(label)
  value.records[0].boxed_warning = longText
  render(<Labels card={value as unknown as import('./contracts').PublicLabel} />)
  await userEvent.click(screen.getByText('boxed warning · stored text'))
  expect(screen.getByText(/Stored exact-product warning/).textContent).toBe(longText)
  expect(screen.getByText(/Label version 3/)).toBeVisible()
})

const lipitor = { ...product, product_ref: 'p_lipitor_old', brand_names: ['Lipitor'], generic_name: 'atorvastatin', product_ndcs: ['0071-0156'], package_ndcs: ['0071-0156-23'] }

async function prepareCohort() {
  const user = userEvent.setup()
  render(<Workspace mode="research_pro" />)
  await user.type(screen.getByLabelText('Local pairing capability'), 'pairing')
  await user.click(screen.getByRole('button', { name: 'Pair Local Session' }))
  const input = await screen.findByLabelText('Search Product by Name, Ingredient or NDC')
  await user.type(input, 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search Directory' }))
  await user.click(await screen.findByRole('button', { name: '+ Add to Cohort' }))
  const tray = () => within(screen.getByRole('region', { name: 'Batch Evidence Overview' }))
  await user.click(tray().getByRole('button', { name: 'Deep Research →' }))
  expect(screen.getByRole('button', { name: 'Execute Deep Evidence Retrieval' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: 'Find Candidate' }))
  await user.click(await screen.findByRole('button', { name: /Xanax.*NDC:/ }))
  await user.click(screen.getByRole('button', { name: 'Confirm Exact Product' }))
  await screen.findByText('✓ Product Identity Locked')
  await user.click(screen.getByRole('button', { name: /Cohort Investigation & Overview/ }))
  vi.mocked(researchApi.search).mockResolvedValueOnce({ state: 'confirmation_required', candidates: [lipitor], results_may_be_incomplete: false })
  await user.clear(screen.getByLabelText('Search Product by Name, Ingredient or NDC'))
  await user.type(screen.getByLabelText('Search Product by Name, Ingredient or NDC'), 'Lipitor')
  await user.click(screen.getByRole('button', { name: 'Search Directory' }))
  await user.click(await screen.findByRole('button', { name: '+ Add to Cohort' }))
  return { user, tray }
}

it('keeps the current confirmed session when reopening the same cohort product', async () => {
  const { user, tray } = await prepareCohort()
  await user.click(within(tray().getByRole('row', { name: /Xanax/ })).getByRole('button', { name: 'Deep Research →' }))
  expect(screen.getByText('✓ Product Identity Locked')).toBeVisible()
  expect(researchApi.close).not.toHaveBeenCalled()
  expect(researchApi.create).toHaveBeenCalledTimes(1)
  expect(researchApi.confirm).toHaveBeenCalledTimes(1)
})

it('switches A to B through a fresh session and confirmation, updating only the correct cohort row', async () => {
  const { user, tray } = await prepareCohort()
  await user.click(screen.getByRole('button', { name: /Deep Single-Product Research/ }))
  await user.click(screen.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }))
  await screen.findByRole('region', { name: 'Research briefing' })
  await user.click(screen.getByRole('button', { name: /Cohort Investigation & Overview/ }))
  const xanaxBefore = tray().getByRole('row', { name: /Xanax/ }).textContent
  await user.click(within(tray().getByRole('row', { name: /Lipitor/ })).getByRole('button', { name: 'Deep Research →' }))
  await screen.findByLabelText('Local pairing capability')
  expect(researchApi.close).toHaveBeenCalledWith(expect.objectContaining({ session_id: 'opaque' }))
  expect(screen.queryByRole('region', { name: 'Research briefing' })).not.toBeInTheDocument()
  expect(screen.queryByText('✓ Product Identity Locked')).not.toBeInTheDocument()

  const nextSession = { session_id: 'session_b', capability: 'cap_b', expires_in: 600, models: [], model_runtime: 'unavailable' as const }
  const fresh = { ...lipitor, product_ref: 'p_lipitor_fresh' }
  vi.mocked(researchApi.create).mockResolvedValueOnce(nextSession)
  vi.mocked(researchApi.search).mockResolvedValueOnce({ state: 'confirmation_required', candidates: [fresh], results_may_be_incomplete: false })
  vi.mocked(researchApi.confirm).mockResolvedValueOnce({ state: 'confirmed', medication: fresh })
  const value: PublicBriefing = { ...briefing, medication: { ...briefing.medication, ...fresh }, sections: [
    { category: 'labels', status: 'available', evidence: null, reason: null },
    { category: 'recalls', status: 'failed', evidence: null, reason: 'tool_timeout' },
    { category: 'faers', status: 'not_requested', evidence: null, reason: null },
  ] }
  vi.mocked(researchApi.result).mockResolvedValueOnce({ state: 'partial', briefing: value, code: null })
  await user.type(screen.getByLabelText('Local pairing capability'), 'pairing')
  await user.click(screen.getByRole('button', { name: 'Pair Local Session' }))
  expect(await screen.findByLabelText('Search Medication to Confirm:')).toHaveValue('0071-0156')
  expect(screen.queryByRole('button', { name: 'Confirm Exact Product' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Execute Deep Evidence Retrieval' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: 'Find Candidate' }))
  expect(researchApi.search).toHaveBeenLastCalledWith(nextSession, '0071-0156')
  expect(await screen.findByRole('button', { name: 'Confirm Exact Product' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: /Lipitor.*NDC:/ }))
  await user.click(screen.getByRole('button', { name: 'Confirm Exact Product' }))
  expect(researchApi.confirm).toHaveBeenLastCalledWith(nextSession, fresh.product_ref)
  await user.click(screen.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }))
  expect(researchApi.run).toHaveBeenLastCalledWith(nextSession, expect.any(String), expect.any(Array), null, false)
  expect(within(await screen.findByRole('region', { name: 'Research briefing' })).getByRole('heading', { name: 'Lipitor' })).toBeVisible()
  await user.click(screen.getByRole('button', { name: /Cohort Investigation & Overview/ }))
  expect(tray().getByRole('row', { name: /Xanax/ }).textContent).toBe(xanaxBefore)
  const row = within(tray().getByRole('row', { name: /Lipitor/ }))
  expect(row.getByText('Available', { exact: true })).toBeVisible()
  expect(row.getByText('Error', { exact: true })).toBeVisible()
  expect(row.getByText('Not evaluated', { exact: true })).toBeVisible()
})

it('discards a late product A poll after switching to B, even while session close is pending', async () => {
  const { user, tray } = await prepareCohort()
  let finish!: (value: Awaited<ReturnType<typeof researchApi.result>>) => void
  let close!: (value: Awaited<ReturnType<typeof researchApi.close>>) => void
  vi.mocked(researchApi.result).mockReturnValueOnce(new Promise(resolve => { finish = resolve }))
  vi.mocked(researchApi.close).mockReturnValueOnce(new Promise(resolve => { close = resolve }))
  await user.click(screen.getByRole('button', { name: /Deep Single-Product Research/ }))
  await user.click(screen.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }))
  await waitFor(() => expect(researchApi.result).toHaveBeenCalled())
  await user.click(screen.getByRole('button', { name: /Cohort Investigation & Overview/ }))
  await user.click(within(tray().getByRole('row', { name: /Lipitor/ })).getByRole('button', { name: 'Deep Research →' }))
  expect(await screen.findByLabelText('Local pairing capability')).toBeVisible()
  await act(async () => { finish({ state: 'partial', briefing, code: null }) })
  expect(screen.queryByRole('region', { name: 'Research briefing' })).not.toBeInTheDocument()
  await act(async () => { close({ state: 'closed', briefing: null, code: null }) })
  await user.type(screen.getByLabelText('Local pairing capability'), 'pairing')
  await user.click(screen.getByRole('button', { name: 'Pair Local Session' }))
  await user.click(screen.getByRole('button', { name: /Cohort Investigation & Overview/ }))
  expect(within(tray().getByRole('table')).getAllByText('Not evaluated', { exact: true })).toHaveLength(8)
  expect(researchApi.run).toHaveBeenCalledTimes(1)
})

it.each(['reference', 'ndc'])('rejects a briefing with a foreign %s before displaying or associating evidence', async mismatch => {
  const medication = mismatch === 'reference' ? { ...briefing.medication, product_ref: 'foreign' } : { ...briefing.medication, product_ndcs: lipitor.product_ndcs }
  vi.mocked(researchApi.result).mockResolvedValueOnce({ state: 'partial', briefing: { ...briefing, medication }, code: null })
  const user = await confirm()
  await user.click(screen.getByRole('button', { name: 'Research selected evidence' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('stored product binding changed')
  expect(screen.queryByRole('region', { name: 'Research briefing' })).not.toBeInTheDocument()
})
