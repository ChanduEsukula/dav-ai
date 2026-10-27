import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../App'
import { EvidencePanel, EvidenceBar } from './EvidencePanel'
import { FaersSummary, LabelSummary } from './ExplorerSummaries'
import fixture from '../test/evidence.json'
import type { DrugEvidence } from '../api/drugCatalog'
import { researchApi } from '../research/client'

vi.mock('../research/client', () => ({ researchApi: { create: vi.fn(), close: vi.fn() } }))
afterEach(() => { window.history.replaceState(null, '', '/'); localStorage.clear(); vi.clearAllMocks() })

it('acknowledges clicking Home without changing the location or resetting the search', () => {
  window.history.replaceState(null, '', '/home')
  render(<App />)
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'Xanax' } })
  fireEvent.click(within(screen.getByRole('navigation', { name: 'Workspace navigation' })).getByRole('link', { name: 'Home' }))
  expect(screen.getByRole('status')).toHaveTextContent('You’re on Home')
  expect(window.location.pathname).toBe('/home')
  expect(screen.getByRole('searchbox')).toHaveValue('Xanax')
})

it('retains a paired research session across client navigation and browser back', async () => {
  window.history.replaceState(null, '', '/ask')
  vi.mocked(researchApi.create).mockResolvedValue({ session_id: 'test', capability: 'private', expires_in: 600, models: [], model_runtime: 'unavailable' })
  vi.mocked(researchApi.close).mockResolvedValue({ state: 'closed', code: null, briefing: null })
  render(<App />)
  fireEvent.change(screen.getByLabelText('Local pairing capability'), { target: { value: 'local-token' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create local session' }))
  const input = await screen.findByLabelText('Brand, ingredient or NDC')
  fireEvent.change(input, { target: { value: 'Xanax' } })
  const nav = screen.getByRole('navigation', { name: 'Workspace navigation' })
  fireEvent.click(within(nav).getByRole('link', { name: 'About' }))
  expect(screen.getByRole('heading', { name: 'Contact the Creator' })).toBeInTheDocument()
  expect(researchApi.close).not.toHaveBeenCalled()
  window.history.replaceState(null, '', '/ask')
  fireEvent.popState(window)
  expect(screen.getByLabelText('Brand, ingredient or NDC')).toHaveValue('Xanax')
  expect(researchApi.create).toHaveBeenCalledTimes(1)
  expect(researchApi.close).not.toHaveBeenCalled()
})

it('renders only the supplied creator accounts', () => {
  window.history.replaceState(null, '', '/about')
  render(<App />)
  expect(screen.getByRole('link', { name: /Email Chandu/ })).toHaveAttribute('href', 'mailto:esukulachandu@gmail.com')
  expect(screen.getByRole('link', { name: /LinkedIn Chandu/ })).toHaveAttribute('href', 'https://www.linkedin.com/in/chandu-esukula-a15454266')
  expect(screen.queryByRole('link', { name: /github/i })).not.toBeInTheDocument()
})

it('expands original evidence with accessible state and collapses it again', () => {
  render(<EvidencePanel kind="recalls" title="Recall history" scope="Product links" summary={<p>Stored summary</p>}><a href="https://api.fda.gov/">Original FDA source</a></EvidencePanel>)
  const button = screen.getByRole('button', { name: 'Expand Recall history' })
  expect(button).toHaveAttribute('aria-expanded', 'false')
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
  fireEvent.click(button)
  expect(button).toHaveAttribute('aria-expanded', 'true')
  expect(screen.getByRole('link')).toBeVisible()
  fireEvent.click(button)
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
})

it('uses exact reaction co-report counts with ingredient and date scope', () => {
  const value = structuredClone(fixture) as DrugEvidence
  render(<FaersSummary evidence={value} />)
  const row = value.adverse_events.records[0].top_reported_reactions[0]
  expect(screen.getByRole('group', { name: `${row.reaction}: ${row.co_report_activity.toLocaleString()} reaction co-report activity` })).toBeInTheDocument()
  expect(screen.getByText(/Not causation, incidence, patient counts or individual risk/)).toBeInTheDocument()
  expect(screen.getByText(/relative to the largest shown value for this ingredient/)).toBeInTheDocument()
})

it('does not turn missing analytics or absent labels into zero risk or no warnings', () => {
  const value = structuredClone(fixture) as DrugEvidence
  value.adverse_events.records[0].analytics = null
  render(<><FaersSummary evidence={value} /><LabelSummary /></>)
  expect(screen.queryByRole('group')).not.toBeInTheDocument()
  expect(screen.getByText(/Missing data is not a zero count/)).toBeInTheDocument()
  expect(screen.getByText(/Missing label text does not mean no warnings exist/)).toBeInTheDocument()
})

it.each([-1, Number.NaN, Number.POSITIVE_INFINITY])('rejects malformed chart count %s', value => {
  render(<EvidenceBar label="Example" value={value} max={100} unit="records" />)
  expect(screen.queryByRole('group')).not.toBeInTheDocument()
})

it('keeps zero counts visible without a minimum fabricated bar length', () => {
  render(<EvidenceBar label="Example" value={0} max={100} unit="records" />)
  expect(screen.getByRole('group')).toHaveAccessibleName('Example: 0 records')
  expect(document.querySelector('.evidence-bar-track > span')).toHaveStyle({ width: '0%' })
})
