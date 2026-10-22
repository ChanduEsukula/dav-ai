import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import Workspace from './Workspace'
import { Briefing } from './Evidence'
import { researchApi } from './client'
import type { PublicBriefing } from './contracts'
import fixture from './briefing.fixture.json'

vi.mock('./client', () => ({ researchApi: { create: vi.fn(), search: vi.fn(), confirm: vi.fn(), run: vi.fn(), result: vi.fn(), cancel: vi.fn(), close: vi.fn() } }))
const product = { product_ref: 'p_owned', brand_names: ['Xanax'], generic_name: 'alprazolam', strength: '.25 mg/1', dosage_form: 'TABLET', routes: ['ORAL'], active_ingredients: ['alprazolam'], product_ndcs: ['0009-0029'], package_ndcs: ['0009-0029-01'] }
const briefing = fixture as unknown as PublicBriefing
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
