import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { searchDrugEvents } from './api/drugEvents'
import { searchRecalls } from './api/recalls'
import App from './App'
import { PAGE_IDS } from './types/navigation'

vi.mock('./api/recalls', async () => {
  const actual = await vi.importActual<typeof import('./api/recalls')>('./api/recalls')
  return { ...actual, searchRecalls: vi.fn() }
})

vi.mock('./api/drugEvents', async () => {
  const actual = await vi.importActual<typeof import('./api/drugEvents')>('./api/drugEvents')
  return { ...actual, searchDrugEvents: vi.fn() }
})

const mockSearchRecalls = vi.mocked(searchRecalls)
const mockSearchDrugEvents = vi.mocked(searchDrugEvents)

beforeEach(() => {
  mockSearchRecalls.mockReset()
  mockSearchDrugEvents.mockReset()
  mockSearchRecalls.mockResolvedValue({
    query: '',
    count: 0,
    limit: 8,
    results: [],
    source_name: 'openFDA Drug Enforcement API',
    endpoint: '/drug/enforcement.json',
    retrieval_timestamp: '2026-06-12T12:00:00Z',
    score_version: 'test',
    medical_disclaimer: 'Test disclaimer',
    audit: {
      audit_id: 'recall-test',
      source_id: 'openfda-recalls',
      module: 'recalls',
      upstream_status: 'ok',
      record_count: 0,
      transform_version: 'test',
    },
  } as Awaited<ReturnType<typeof searchRecalls>>)
  mockSearchDrugEvents.mockResolvedValue({
    query: '',
    count: 0,
    limit: 8,
    top_reactions: [],
    source_name: 'openFDA Drug Event API',
    endpoint: '/drug/event.json',
    retrieval_timestamp: '2026-06-12T12:00:00Z',
    medical_disclaimer: 'Test disclaimer',
    faers_disclaimer: 'Test FAERS disclaimer',
    audit: {
      audit_id: 'drug-test',
      source_id: 'openfda-faers',
      module: 'drug-events',
      upstream_status: 'ok',
      record_count: 0,
      transform_version: 'test',
    },
    intelligence_score: {
      score: 0,
      label: 'Limited signal',
      data_confidence: 'Limited',
      top_reaction_concentration: 0,
      review_priority: 'Review source records',
      score_version: 'test',
      limitations: [],
    },
    reaction_categories: [],
    reaction_classifier_version: 'test',
    trend_snapshot: {
      label: 'No comparison available',
      current_record_count: 0,
      previous_record_count: null,
      previous_audit_id: null,
      previous_created_at: null,
      explanation: 'No prior snapshot in test data.',
      limitation: 'Test data only.',
      trend_version: 'test',
    },
  } as Awaited<ReturnType<typeof searchDrugEvents>>)
  window.history.replaceState(null, '', '/')
})

test('renders Dav AI landing page', () => {
  render(<App />)

  expect(screen.getByRole('button', { name: /Dav AI home/i })).toBeInTheDocument()

  expect(screen.getByRole('heading', { name: /Public safety/i })).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /Pharmacy Safety.*Recalls \+ adverse-event patterns/i,
    }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /Food Safety.*Food & supplement recalls/i,
    }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /Cosmetic Safety.*Public cosmetic-event reports/i,
    }),
  ).toBeInTheDocument()

  expect(screen.getByRole('button', { name: /How it works/i })).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Safety Record Search/i }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Choose a safety lens/i }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Public-data intelligence at a glance/i }),
  ).toBeInTheDocument()

  expect(
    screen.queryByRole('heading', { name: /Search public FDA recall signals/i }),
  ).not.toBeInTheDocument()

  expect(
    screen.queryByRole('heading', {
      name: /Explore public FAERS adverse-event reporting patterns/i,
    }),
  ).not.toBeInTheDocument()

  expect(screen.queryByText('24.6K')).not.toBeInTheDocument()
  expect(screen.queryByText('1.2K')).not.toBeInTheDocument()
  expect(screen.queryByText('98%')).not.toBeInTheDocument()
  expect(screen.getByText('Public source records')).toBeInTheDocument()
  expect(screen.getByText('Source + retrieval context')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /Explain These Results/i })).not.toBeInTheDocument()
})

test('does not expose placeholder account pages in the main demo navigation', () => {
  render(<App />)

  expect(screen.queryByRole('button', { name: /Profile/i })).not.toBeInTheDocument()

  expect(screen.queryByRole('button', { name: /Sign Up/i })).not.toBeInTheDocument()
})

test('renders simplified navigation with advanced workflows still available', () => {
  render(<App />)

  const mainNav = screen.getByRole('navigation', { name: /Main navigation/i })
  const mainPages = within(screen.getByLabelText('Main pages'))
  const advancedWorkflows = within(screen.getByLabelText('Advanced workflows'))
  const informationPages = within(screen.getByLabelText('Information pages'))

  for (const label of ['Home', 'Search', 'Saved Searches', 'About']) {
    expect(mainPages.getByRole('button', { name: label })).toBeInTheDocument()
  }

  for (const label of [
    'Pharmacy Safety',
    'Food Safety',
    'Cosmetic Safety',
    'Audit',
    'Sources',
    'System',
  ]) {
    expect(advancedWorkflows.getByRole('button', { name: label })).toBeInTheDocument()
  }

  for (const label of ['FAQ', 'Help']) {
    expect(informationPages.getByRole('button', { name: label })).toBeInTheDocument()
  }

  expect(within(mainNav).queryByRole('button', { name: 'Public Safety' })).not.toBeInTheDocument()
  expect(within(mainNav).queryByRole('button', { name: 'Monitors' })).not.toBeInTheDocument()
})

test('opens ProductScan from the homepage experiment entry without adding primary nav', () => {
  render(<App />)

  const mainNav = screen.getByRole('navigation', { name: /Main navigation/i })
  expect(within(mainNav).queryByRole('button', { name: /ProductScan/i })).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: /Open ProductScan/i }))

  expect(
    screen.getByRole('heading', { name: /Review label text before searching public records/i }),
  ).toBeInTheDocument()
  expect(new URLSearchParams(window.location.search).get('page')).toBe(PAGE_IDS.PRODUCT_SCAN)
})

test('renders focused navigation groups in the pill nav', () => {
  render(<App />)

  for (const label of ['Home', 'Search', 'Saved Searches', 'About']) {
    const navButton = screen.getByRole('button', { name: label })

    expect(navButton.closest('.nav-links')).toBeInTheDocument()
    expect(navButton.closest('.nav-links-secondary')).not.toBeInTheDocument()
    expect(navButton.closest('.nav-actions')).not.toBeInTheDocument()
  }

  for (const label of [
    'Pharmacy Safety',
    'Food Safety',
    'Cosmetic Safety',
    'Audit',
    'Sources',
    'System',
  ]) {
    const navButton = screen.getByRole('button', { name: label })

    expect(navButton.closest('.nav-links-secondary')).toBeInTheDocument()
  }

  for (const label of ['FAQ', 'Help']) {
    const navButton = screen.getByRole('button', { name: label })

    expect(navButton.closest('.nav-actions')).toBeInTheDocument()
  }

  expect(screen.queryByRole('button', { name: 'Public Safety' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Monitors' })).not.toBeInTheDocument()
})

test('shows Help Docs Search on the Help page', () => {
  window.history.replaceState(null, '', '/?page=help')

  render(<App />)

  expect(
    screen.getByRole('heading', { name: /Use it as a review tool, not medical advice/i }),
  ).toBeInTheDocument()
  expect(screen.getByLabelText(/Search Dav AI docs/i)).toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: /Find cited snippets from Dav AI docs/i }),
  ).toBeInTheDocument()
})

test('does not show Help Docs Search on the About page', () => {
  window.history.replaceState(null, '', '/?page=about')

  render(<App />)

  expect(screen.getByRole('heading', { name: /Healthcare safety intelligence/i })).toBeInTheDocument()
  expect(screen.queryByLabelText(/Search Dav AI docs/i)).not.toBeInTheDocument()
  expect(
    screen.queryByRole('heading', { name: /Find cited snippets from Dav AI docs/i }),
  ).not.toBeInTheDocument()
})

test('does not show Help Docs Search on the FAQ page', () => {
  window.history.replaceState(null, '', '/?page=faq')

  render(<App />)

  expect(
    screen.getByRole('heading', { name: /Clear answers without crowding the page/i }),
  ).toBeInTheDocument()
  expect(screen.queryByLabelText(/Search Dav AI docs/i)).not.toBeInTheDocument()
  expect(
    screen.queryByRole('heading', { name: /Find cited snippets from Dav AI docs/i }),
  ).not.toBeInTheDocument()
})

test('ignores old placeholder account page URLs', () => {
  window.history.replaceState(null, '', '/?page=signup')

  render(<App />)

  expect(screen.getByRole('heading', { name: /Public safety/i })).toBeInTheDocument()

  expect(screen.queryByText(/Early access placeholder/i)).not.toBeInTheDocument()
})

test('falls back to the home page for unknown page query values', () => {
  window.history.replaceState(null, '', '/?page=unknown-demo-page&q=Xanax')

  render(<App />)

  expect(screen.getByRole('heading', { name: /Public safety/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Home' })).toHaveAttribute(
    'aria-current',
    'page',
  )
  expect(mockSearchRecalls).not.toHaveBeenCalled()
  expect(mockSearchDrugEvents).not.toHaveBeenCalled()
})

test('updates a detail page when browser history changes only the query', async () => {
  window.history.replaceState(null, '', '/?page=pharmacy-safety&q=Xanax')
  render(<App />)

  expect(
    await screen.findByRole('heading', { name: /Safety review for Xanax/i }),
  ).toBeInTheDocument()

  act(() => {
    window.history.pushState(null, '', '/?page=pharmacy-safety&q=Metformin')
    window.dispatchEvent(new PopStateEvent('popstate'))
  })

  expect(
    await screen.findByRole('heading', { name: /Safety review for Metformin/i }),
  ).toBeInTheDocument()
  expect(mockSearchRecalls).toHaveBeenLastCalledWith('Metformin', 8, 'score')
})

test('uses canonical active navigation and clears stale audit parameters', async () => {
  window.history.replaceState(
    null,
    '',
    '/?page=pharmacy-safety&q=Xanax&audit_id=stale-audit',
  )
  render(<App />)

  expect(
    await screen.findByRole('heading', { name: /Safety review for Xanax/i }),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Pharmacy Safety' })).toHaveAttribute(
    'aria-current',
    'page',
  )

  fireEvent.click(screen.getByRole('button', { name: 'Food Safety' }))

  expect(
    await screen.findByRole('heading', {
      name: /Search food and supplement safety records/i,
    }),
  ).toBeInTheDocument()
  expect(new URLSearchParams(window.location.search).get('audit_id')).toBeNull()
})

test('restores normalized and original queries from a deep link', async () => {
  window.history.replaceState(
    null,
    '',
    '/?page=pharmacy-safety&q=xanax&raw_q=xanex',
  )
  render(<App />)

  expect(
    await screen.findByRole('heading', { name: /Safety review for xanax/i }),
  ).toBeInTheDocument()
  expect(screen.getByLabelText(/Search pharmacy records/i)).toHaveValue('xanex')
  expect(
    screen.getByText(/Showing results for 'xanax' based on your search 'xanex'/i),
  ).toBeInTheDocument()
  expect(mockSearchRecalls).toHaveBeenCalledWith('xanax', 8, 'score')
})
