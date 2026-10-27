import { fireEvent, render, screen, within } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { MedicationSummary, CompactProducts } from './MedicationDiscovery'
import fixture from '../test/medication-overview.fixture.json'
import type { MedicationOverview } from '../api/drugCatalog'

const value = fixture as MedicationOverview

it('shows bounded medication-level evidence before any exact product is selected', () => {
  render(<MedicationSummary value={value} mode="everyday" />)
  expect(screen.getByRole('heading', { name: /Xanax.*alprazolam/i })).toBeInTheDocument()
  expect(screen.getByText('distinct linked historical records')).toBeInTheDocument()
  expect(screen.getAllByText('Failed Dissolution Specifications')[0]).toBeInTheDocument()
  expect(screen.getAllByText('Subpotent Drug')[0]).toBeInTheDocument()
  expect(screen.getByText(/stored ingredient-report associations/)).toBeInTheDocument()
  expect(screen.getByText(/Not brand-specific patients, incidence or causation/)).toBeInTheDocument()
  expect(screen.queryByText('confirmed product', { exact: true })).not.toBeInTheDocument()
})

it('keeps compact product identities distinct and filters by actual strength', () => {
  const select = vi.fn()
  render(<CompactProducts products={value.products} query="Xanax" mode="everyday" onSelect={select} />)
  expect(screen.getAllByRole('button', { name: /^Select .*NDC/ })).toHaveLength(9)
  const strength = value.products[0].strength!
  fireEvent.keyDown(screen.getByRole('combobox', {name:'Strength'}), { key:'ArrowDown' })
  fireEvent.click(screen.getByRole('option', {name:strength.replace(/^\./,'0.').replace('/', ' / ')}))
  const expected = value.products.filter(product => product.strength === strength)
  expect(screen.getAllByRole('button', { name: /^Select .*NDC/ })).toHaveLength(expected.length)
  fireEvent.click(screen.getAllByRole('button', { name: /^Select .*NDC/ })[0])
  expect(expected.map(product => product.id)).toContain(select.mock.calls[0][0].id)
})

it('renders a denser semantic table and provenance controls in Research Pro', () => {
  render(<CompactProducts products={value.products} query="Xanax" mode="research_pro" onSelect={vi.fn()} />)
  expect(screen.getByRole('table', { name: 'Matching products and exact source identifiers' })).toBeInTheDocument()
  expect(screen.getByLabelText('Sort products')).toBeInTheDocument()
  expect(screen.getByLabelText('Product or package NDC')).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('Product or package NDC'), { target: { value: '58151-505' } })
  expect(screen.getAllByRole('button', { name: /^Select .*NDC/ })).toHaveLength(1)
  expect(screen.getByText(/Xanax XR · separate named formulation/)).toBeInTheDocument()
})

it('expands recall reasons, source links and product-specific lot restrictions', () => {
  render(<MedicationSummary value={value} mode="research_pro" />)
  fireEvent.click(screen.getByRole('button', { name: 'Expand Historical recalls' }))
  const panel = screen.getByRole('region', { name: 'Historical recalls' })
  expect(within(panel).getByText(/Recalling firm: Viatris/)).toBeVisible()
  expect(within(panel).getAllByText(/Lot scope:/).length).toBeGreaterThan(0)
  expect(within(panel).getAllByRole('link', { name: /Original FDA source/ })).toHaveLength(2)
})
