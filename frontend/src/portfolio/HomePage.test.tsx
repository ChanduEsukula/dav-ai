import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../App'
import { STORAGE_KEY_EXPERIENCE_MODE } from '../components/experienceState'

afterEach(() => { window.history.replaceState(null, '', '/'); localStorage.clear() })

it('connects the curved hero search to the existing Explorer query contract', () => {
  window.history.replaceState(null, '', '/home')
  render(<App />)
  const search = screen.getByRole('search', { name: 'Find a medication' })
  expect(search).toHaveAttribute('action', '/')
  expect(search).toHaveAttribute('method', 'get')
  const input = within(search).getByRole('searchbox', { name: 'Medication name or NDC' })
  expect(input).toBeRequired()
  expect(input).toHaveAttribute('maxlength', '200')
  fireEvent.change(input, { target: { value: '0009-0029' } })
  expect(new FormData(search as HTMLFormElement).get('q')).toBe('0009-0029')
  expect(within(search).getByRole('button', { name: 'Search medications' })).toHaveAttribute('type', 'submit')
})

for (const path of ['/home', '/', '/ask', '/overview', '/about', '/faq']) {
  it(`retains the same brand, routes and persisted selector on ${path}`, () => {
    localStorage.setItem(STORAGE_KEY_EXPERIENCE_MODE, 'research_pro')
    window.history.replaceState(null, '', path)
    render(<App />)
    expect(screen.getByRole('link', { name: 'Dav AI home' })).toHaveTextContent(/^Dav AI$/)
    const nav = screen.getByRole('navigation', { name: 'Workspace navigation' })
    expect(within(nav).getAllByRole('link').map(link => link.getAttribute('href')))
      .toEqual(['/home', '/', '/ask', '/overview', '/faq', '/about', '/about#contact-creator'])
    const group = screen.getByRole('group', { name: 'Experience' })
    expect(within(group).getByRole('button', { name: 'Research Pro' })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(within(group).getByRole('button', { name: 'Everyday' }))
    expect(localStorage.getItem(STORAGE_KEY_EXPERIENCE_MODE)).toBe('everyday')
  })
}

it('renders a noninteractive static scene without WebGL and retains truthful source limits', () => {
  window.history.replaceState(null, '', '/home')
  render(<App />)
  expect(screen.getByTestId('orb-static')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /orb|capsule|download/i })).not.toBeInTheDocument()
  expect(screen.getByText(/FAERS reports do not establish causation, incidence or individual patient risk/)).toBeInTheDocument()
  expect(screen.getByText(/Missing data does not mean an event or warning never existed/)).toBeInTheDocument()
  expect(screen.queryByText(/academic project|student project|graduate AI portfolio/)).not.toBeInTheDocument()
  for (const kind of ['labels', 'recalls', 'faers']) {
    const card = document.querySelector(`.evidence-${kind}`)!
    expect(card).toHaveAttribute('href', '#explore-data')
    expect(document.getElementById('explore-data')).not.toBeNull()
  }
})

vi.mock('../api/drugCatalog', async importOriginal => ({
  ...await importOriginal<typeof import('../api/drugCatalog')>(),
  getDataInventory: vi.fn().mockRejectedValue(new Error('Inventory unavailable in this UI-only test')),
}))
