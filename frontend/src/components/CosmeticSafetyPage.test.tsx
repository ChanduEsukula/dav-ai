import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  searchCosmeticEvents,
  type CosmeticEventSearchResponse,
} from '../api/cosmeticEvents'
import CosmeticSafetyPage from './CosmeticSafetyPage'

vi.mock('../api/cosmeticEvents', async () => {
  const actual = await vi.importActual<typeof import('../api/cosmeticEvents')>(
    '../api/cosmeticEvents',
  )

  return {
    ...actual,
    searchCosmeticEvents: vi.fn(),
  }
})

const mockSearchCosmeticEvents = vi.mocked(searchCosmeticEvents)
const mockGoToPage = vi.fn()

const sunscreenProduct = 'Solstice Daily Mineral Sunscreen SPF 50'

const cosmeticResponse: CosmeticEventSearchResponse = {
  query: 'Sunscreen',
  count: 2,
  limit: 8,
  source_name: 'openFDA Cosmetic Event API',
  endpoint: 'https://api.fda.gov/food/event.json',
  retrieval_timestamp: '2026-06-12T12:00:00Z',
  medical_disclaimer: 'This is not medical advice.',
  cosmetic_disclaimer: 'Cosmetic reports do not prove causation.',
  audit: {
    audit_id: 'cosmetic-audit',
    source_id: 'openfda-cosmetic-event',
    module: 'CosmeticSignal',
    upstream_status: 'success',
    record_count: 2,
    transform_version: 'cosmetic-event-v1',
    source_snapshot_status: null,
    source_pull_id: null,
    source_payload_hash: null,
  },
  signal_score: {
    score: 58,
    label: 'Moderate',
    data_confidence: 'Limited',
    top_reaction_concentration: 60,
    review_priority: 'Watch',
    score_version: 'cosmetic-signal-v1',
    limitations: [
      'Reports may be incomplete or duplicated.',
      'Reports do not establish product causation.',
    ],
  },
  top_reactions: [
    { reaction: 'RASH', count: 6 },
    { reaction: 'BURNING SENSATION', count: 3 },
    { reaction: 'ERYTHEMA', count: 1 },
  ],
  recall_count: 1,
  recall_source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
  recall_source_status: 'success',
  recall_source_error: null,
  recall_notices: [
    {
      title: 'FDA public notice for Solstice Daily Mineral Sunscreen SPF 50',
      product_name: 'Daily Mineral Sunscreen SPF 50',
      brand_name: 'Solstice',
      company_name: 'Solstice Labs',
      category: 'Cosmetics',
      reason: 'Potential product quality concern',
      remedy: 'Consumers should stop using the affected product.',
      published_date: '2026-06-02',
      record_url: 'https://www.fda.gov/safety/example-sunscreen-notice',
      source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
      source_kind: 'normalized_public_notice',
      source_type: 'normalized official public notice',
      extraction_confidence: 'high',
    },
  ],
  records: [
    {
      report_number: 'CAERS-2026-001',
      report_date: '20260601',
      serious: 'No',
      outcomes: ['Other'],
      reactions: ['RASH', 'BURNING SENSATION'],
      products: [
        {
          brand_name: sunscreenProduct,
          name_brand: null,
          industry_code: '54',
          industry_name: 'Vit/Min/Prot/Unconv Diet(Human/Animal)',
        },
      ],
    },
    {
      report_number: 'CAERS-2026-002',
      report_date: '20260518',
      serious: 'Yes',
      outcomes: ['Hospitalization'],
      reactions: ['ERYTHEMA'],
      products: [
        {
          brand_name: null,
          name_brand: 'Sun Veil Face Lotion',
          industry_code: '53',
          industry_name: 'Cosmetics',
        },
        {
          brand_name: null,
          name_brand: null,
          industry_code: '53',
          industry_name: 'Skin preparations',
        },
      ],
    },
  ],
}

const emptyCosmeticResponse: CosmeticEventSearchResponse = {
  ...cosmeticResponse,
  count: 0,
  records: [],
  top_reactions: [],
  signal_score: {
    ...cosmeticResponse.signal_score,
    score: 0,
    label: 'No signal',
    top_reaction_concentration: 0,
  },
  audit: {
    ...cosmeticResponse.audit,
    record_count: 0,
  },
}

function renderCosmeticPage(initialQuery = 'Sunscreen') {
  return render(
    <CosmeticSafetyPage
      initialQuery={initialQuery}
      goToPage={mockGoToPage}
    />,
  )
}

beforeEach(() => {
  mockGoToPage.mockReset()
  mockSearchCosmeticEvents.mockReset()
  mockSearchCosmeticEvents.mockResolvedValue(cosmeticResponse)
  window.history.replaceState(null, '', '?page=cosmetic-safety&q=Sunscreen')
})

test('renders the Cosmetic Safety dashboard and multiple reports for Sunscreen', async () => {
  renderCosmeticPage()

  expect(
    await screen.findByRole('heading', { name: /Safety review for Sunscreen/i }),
  ).toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: /Matched cosmetic reports/i }),
  ).toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: /Public reporting pattern/i }),
  ).toBeInTheDocument()
  expect(screen.getByTitle(sunscreenProduct)).toBeInTheDocument()
  expect(screen.getByTitle('Sun Veil Face Lotion')).toBeInTheDocument()
  expect(screen.getByText(/Showing 2 of 2 returned reports/i)).toBeInTheDocument()
  expect(screen.getByText(/FDA public notices/i)).toBeInTheDocument()
  expect(
    screen.getByTitle('FDA public notice for Solstice Daily Mineral Sunscreen SPF 50'),
  ).toBeInTheDocument()
  expect(screen.getAllByText('Normalized public notice').length).toBeGreaterThan(0)
})

test('loads normalized Cosmetic reports with limit 8', async () => {
  window.history.replaceState(null, '', '?page=cosmetic-safety&q=Mineral%20Sunscreen')
  renderCosmeticPage('  Mineral   Sunscreen  ')

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledWith('Mineral Sunscreen', 8)
  })
})

test('empty input falls back to the submitted Cosmetic query', async () => {
  const user = userEvent.setup()
  renderCosmeticPage()

  await screen.findByRole('heading', { name: /Safety review for Sunscreen/i })
  await user.clear(screen.getByLabelText(/Search cosmetic safety records/i))
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledTimes(2)
  })
  expect(mockSearchCosmeticEvents).toHaveBeenLastCalledWith('Sunscreen', 8)
})

test('spaces-only input falls back to the submitted Cosmetic query', async () => {
  const user = userEvent.setup()
  renderCosmeticPage()

  await screen.findByRole('heading', { name: /Safety review for Sunscreen/i })
  const input = screen.getByLabelText(/Search cosmetic safety records/i)
  await user.clear(input)
  await user.type(input, '   ')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledTimes(2)
  })
  expect(mockSearchCosmeticEvents).toHaveBeenLastCalledWith('Sunscreen', 8)
})

test('empty input with no submitted query shows quiet Cosmetic guidance', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=cosmetic-safety')
  renderCosmeticPage('')

  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    screen.getByText(
      /Enter a cosmetic, brand, ingredient, or personal-care product to search public reports/i,
    ),
  ).toBeInTheDocument()
  expect(mockSearchCosmeticEvents).not.toHaveBeenCalled()
})

test('an example chip runs a new Cosmetic search and clears guidance', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=cosmetic-safety')
  renderCosmeticPage('')

  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(screen.getByText(/Enter a cosmetic, brand, ingredient/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Moisturizer' }))

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledWith('Moisturizer', 8)
  })
  expect(screen.queryByText(/Enter a cosmetic, brand, ingredient/i)).not.toBeInTheDocument()
})

test('a Xanax Cosmetic search suggests Pharmacy Safety', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=cosmetic-safety')
  renderCosmeticPage('')

  await user.type(screen.getByLabelText(/Search cosmetic safety records/i), 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    await screen.findByText(/This looks more like a Pharmacy Safety search/i),
  ).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Open Pharmacy Safety' }))
  expect(mockGoToPage).toHaveBeenCalledWith('pharmacy-safety', 'Xanax')
})

test('a Chicken Cosmetic search suggests Food & Supplement Safety', async () => {
  const user = userEvent.setup()
  mockSearchCosmeticEvents.mockResolvedValue(emptyCosmeticResponse)
  window.history.replaceState(null, '', '?page=cosmetic-safety')
  renderCosmeticPage('')

  await user.type(screen.getByLabelText(/Search cosmetic safety records/i), 'Chicken')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  const suggestion = await screen.findByText(
    /This looks more like a Food & Supplement Safety search/i,
  )
  const suggestionBox = suggestion.closest('.safety-route-suggestion')
  const examples = screen.getByLabelText('Example cosmetic searches')
  expect(suggestion.closest('.cosmetic-overview')).toBeInTheDocument()
  expect(
    suggestionBox!.compareDocumentPosition(examples) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).not.toBe(0)
  expect(
    screen.getByText(/This looks better suited for Food & Supplement Safety/i),
  ).toBeInTheDocument()
  expect(
    screen.queryByText(/No cosmetic-event reports returned for this exact search/i),
  ).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Open Food & Supplement Safety' }))
  expect(mockGoToPage).toHaveBeenCalledWith('food-safety', 'Chicken')
})

test('zero reports show calm guidance without claiming the cosmetic is safe', async () => {
  mockSearchCosmeticEvents.mockResolvedValue(emptyCosmeticResponse)
  renderCosmeticPage('Unknown cream')

  expect(
    await screen.findByText(/No cosmetic-event reports returned for this exact search/i),
  ).toBeInTheDocument()
  expect(screen.getByText(/No result does not prove a cosmetic is safe/i)).toBeInTheDocument()
  expect(screen.queryByText(/This cosmetic is safe/i)).not.toBeInTheDocument()
  expect(screen.queryByText(/0\s*\/\s*100/i)).not.toBeInTheDocument()
  expect(screen.getAllByText(/No returned reports/i)).not.toHaveLength(0)
  expect(screen.getAllByText('Not assessable')).not.toHaveLength(0)
  expect(screen.queryByText('Limited')).not.toBeInTheDocument()
})

test('uses the report number when a Cosmetic report has no product title fields', async () => {
  mockSearchCosmeticEvents.mockResolvedValue({
    ...cosmeticResponse,
    count: 1,
    recall_count: 1,
  recall_source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
  recall_source_status: 'success',
  recall_source_error: null,
  recall_notices: [
    {
      title: 'FDA public notice for Solstice Daily Mineral Sunscreen SPF 50',
      product_name: 'Daily Mineral Sunscreen SPF 50',
      brand_name: 'Solstice',
      company_name: 'Solstice Labs',
      category: 'Cosmetics',
      reason: 'Potential product quality concern',
      published_date: '2026-06-02',
      record_url: 'https://www.fda.gov/safety/example-sunscreen-notice',
      source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
    },
  ],
  records: [
      {
        ...cosmeticResponse.records[0],
        report_number: 'CAERS-FALLBACK-001',
        products: [],
      },
    ],
    audit: {
      ...cosmeticResponse.audit,
      record_count: 1,
    },
  })

  renderCosmeticPage()

  expect(await screen.findByTitle('Cosmetic report CAERS-FALLBACK-001')).toBeInTheDocument()
})

test('normalizes hairdye and preserves the original Cosmetic query', async () => {
  window.history.replaceState(null, '', '?page=cosmetic-safety&q=hairdye')
  renderCosmeticPage('hairdye')

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledWith('hair dye', 8)
  })
  expect(
    screen.getByText(/Showing results for 'hair dye' based on your search 'hairdye'/i),
  ).toBeInTheDocument()
  expect(screen.getByLabelText(/Search cosmetic safety records/i)).toHaveValue('hairdye')
  expect(new URLSearchParams(window.location.search).get('q')).toBe('hair dye')
  expect(new URLSearchParams(window.location.search).get('raw_q')).toBe('hairdye')
})

test('an API failure shows the public source availability error', async () => {
  mockSearchCosmeticEvents.mockRejectedValue(new Error('Source unavailable'))
  renderCosmeticPage()

  expect(
    await screen.findByText(
      /Unable to load public records. Check backend\/source availability/i,
    ),
  ).toBeInTheDocument()
})

test('a changed route initialQuery reloads the normalized Cosmetic query', async () => {
  const { rerender } = renderCosmeticPage()

  await screen.findByRole('heading', { name: /Safety review for Sunscreen/i })
  window.history.replaceState(null, '', '?page=cosmetic-safety&q=Hair%20dye')
  rerender(
    <CosmeticSafetyPage
      initialQuery="  Hair   dye "
      goToPage={mockGoToPage}
    />,
  )

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenLastCalledWith('Hair dye', 8)
  })
  expect(
    screen.getByRole('heading', { name: /Safety review for Hair dye/i }),
  ).toBeInTheDocument()
})

test('a Cosmetic report row expands and collapses its report details', async () => {
  const user = userEvent.setup()
  renderCosmeticPage()

  const product = await screen.findByTitle(sunscreenProduct)
  const details = product.closest('details')
  expect(details).not.toHaveAttribute('open')

  await user.click(product)
  expect(details).toHaveAttribute('open')
  expect(screen.getByText('Industry code: 54')).toBeInTheDocument()

  await user.click(product)
  expect(details).not.toHaveAttribute('open')
})

test('top reactions and signal limitations render in the Cosmetic right rail', async () => {
  renderCosmeticPage()

  expect(await screen.findAllByText('RASH')).not.toHaveLength(0)
  expect(screen.getByText('BURNING SENSATION')).toBeInTheDocument()
  expect(screen.getByText('Reports may be incomplete or duplicated.')).toBeInTheDocument()
  expect(screen.getByText('Reports do not establish product causation.')).toBeInTheDocument()
  expect(screen.getByText('Watch')).toBeInTheDocument()
  expect(screen.getAllByText('Limited')).not.toHaveLength(0)
})
