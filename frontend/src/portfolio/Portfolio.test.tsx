import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../App'

afterEach(() => { window.history.replaceState(null, '', '/'); localStorage.clear() })

it('restores the landing and educational source workflow without obsolete services or metrics', () => {
  window.history.replaceState(null, '', '/home')
  render(<App />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Real FDA data. Clearer answers.')
  expect(screen.getByRole('link', { name: /Explore medications/ })).toHaveAttribute('href', '/')
  expect(screen.getByRole('heading', { name: /Inside Dav AI/i })).toBeInTheDocument()
  expect(screen.getByText(/Human review is required/)).toBeInTheDocument()
  expect(screen.queryByText(/foodsignal|saved monitors|risk score/i)).not.toBeInTheDocument()
  expect(screen.getByRole('img', { name: /Not live results/ })).toBeInTheDocument()
})

it('keeps the root Explorer and account-free search', () => {
  window.history.replaceState(null, '', '/')
  render(<App />)
  expect(screen.getByRole('search')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Dav AI home' })).toHaveAttribute('href', '/home')
})

it('keeps FAQ disclosures native and removes obsolete scoring claims', () => {
  window.history.replaceState(null, '', '/faq')
  render(<App />)
  const question = screen.getByText('Is Dav AI FDA approved?')
  expect(question.closest('summary')).toBeInTheDocument()
  expect(question.closest('details')).not.toHaveAttribute('open')
  expect(screen.getByText(/ingredient-level reporting associations, not selected-NDC observations/)).toBeInTheDocument()
  expect(screen.queryByText(/Recall Review Priority/)).not.toBeInTheDocument()
})

it('supports historical informational links', () => {
  window.history.replaceState(null, '', '/?page=about')
  render(<App />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Better questions.Traceable evidence.')
  expect(document.title).toBe('About · Dav AI')
})

it('closes mobile navigation with Escape and restores trigger focus', () => {
  render(<App />)
  const trigger = screen.getByRole('button', { name: /Menu/ })
  fireEvent.click(trigger)
  expect(trigger).toHaveAttribute('aria-expanded', 'true')
  fireEvent.keyDown(screen.getByRole('navigation', { name: 'Workspace navigation' }), { key: 'Escape' })
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
  expect(trigger).toHaveFocus()
})

it('provides a main-content skip target in both Ask modes', () => {
  window.history.replaceState(null, '', '/ask')
  render(<App />)
  expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
  fireEvent.click(screen.getByRole('button', { name: /Research Pro/ }))
  expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
  expect(screen.getByRole('heading', { name: 'Pharmaceutical Evidence Workspace' })).toBeInTheDocument()
})

vi.mock('../api/drugCatalog', async importOriginal => ({
  ...await importOriginal<typeof import('../api/drugCatalog')>(),
  getDataInventory: vi.fn().mockRejectedValue(new Error('Inventory unavailable in this UI-only test')),
}))
