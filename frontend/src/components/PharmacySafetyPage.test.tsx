import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import { searchRecalls, type RecallSearchResponse } from '../api/recalls'
import PharmacySafetyPage from './PharmacySafetyPage'

vi.mock('../api/recalls', async () => {
  const actual = await vi.importActual<typeof import('../api/recalls')>('../api/recalls')

  return {
    ...actual,
    searchRecalls: vi.fn(),
  }
})

vi.mock('../api/drugEvents', async () => {
  const actual = await vi.importActual<typeof import('../api/drugEvents')>('../api/drugEvents')

  return {
    ...actual,
    searchDrugEvents: vi.fn(),
  }
})

const mockSearchRecalls = vi.mocked(searchRecalls)
const mockSearchDrugEvents = vi.mocked(searchDrugEvents)
const mockGoToPage = vi.fn()

const longProductName =
  'Alprazolam tablets, 0.5 mg, packaged in 100-count bottles with additional distribution details and labeling information'

const recallResponse: RecallSearchResponse = {
  query: 'Xanax',
  count: 1,
  limit: 8,
  source_name: 'openFDA Drug Enforcement API',
  endpoint: 'https://api.fda.gov/drug/enforcement.json',
  retrieval_timestamp: '2026-06-12T12:00:00Z',
  score_version: 'recall-score-v1',
  sort: 'score',
  medical_disclaimer: 'Public data only.',
  audit: {
    audit_id: 'recall-audit',
    source_id: 'openfda-drug-enforcement',
    module: 'RecallRadar',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'recall-transform-v1',
  },
  results: [
    {
      recall_number: 'D-1234-2026',
      product_description: longProductName,
      reason_for_recall: 'Labeling issue',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260520',
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Pharma',
      risk_score: {
        score: 64,
        label: 'Moderate',
        components: {
          classification_score: 25,
          status_score: 15,
          recency_score: 14,
          scope_score: 10,
        },
        score_version: 'recall-score-v1',
      },
      source: {
        name: 'openFDA Drug Enforcement API',
        endpoint: 'https://api.fda.gov/drug/enforcement.json',
        retrieval_timestamp: '2026-06-12T12:00:00Z',
      },
    },
  ],
}

const drugResponse: DrugEventSearchResponse = {
  query: 'Xanax',
  count: 8,
  limit: 8,
  source_name: 'openFDA Drug Event API',
  endpoint: 'https://api.fda.gov/drug/event.json',
  retrieval_timestamp: '2026-06-12T12:00:00Z',
  medical_disclaimer: 'Public data only.',
  faers_disclaimer: 'Reports do not prove causation.',
  audit: {
    audit_id: 'drug-audit',
    source_id: 'openfda-drug-event',
    module: 'DrugSignal',
    upstream_status: 'success',
    record_count: 8,
    transform_version: 'drug-event-transform-v1',
  },
  intelligence_score: {
    score: 52,
    label: 'Moderate',
    data_confidence: 'Limited',
    top_reaction_concentration: 50,
    review_priority: 'Watch',
    score_version: 'drug-signal-v1',
    limitations: ['Reports do not prove causation.'],
  },
  reaction_categories: [],
  reaction_classifier_version: 'reaction-classifier-v1',
  trend_snapshot: {
    label: 'Stable',
    current_record_count: 8,
    previous_record_count: null,
    previous_audit_id: null,
    previous_created_at: null,
    explanation: 'No prior snapshot.',
    limitation: 'Public search snapshot only.',
    trend_version: 'drug-trend-v1',
  },
  top_reactions: [
    { reaction: 'SOMNOLENCE', count: 4 },
    { reaction: 'DIZZINESS', count: 2 },
  ],
}

const emptyRecallResponse: RecallSearchResponse = {
  ...recallResponse,
  count: 0,
  results: [],
  audit: {
    ...recallResponse.audit,
    record_count: 0,
  },
}

const emptyDrugResponse: DrugEventSearchResponse = {
  ...drugResponse,
  count: 0,
  top_reactions: [],
  audit: {
    ...drugResponse.audit,
    record_count: 0,
  },
}

function renderPharmacyPage(initialQuery = 'Xanax') {
  return render(
    <PharmacySafetyPage initialQuery={initialQuery} goToPage={mockGoToPage} />,
  )
}

beforeEach(() => {
  mockGoToPage.mockReset()
  mockSearchRecalls.mockReset()
  mockSearchDrugEvents.mockReset()
  mockSearchRecalls.mockResolvedValue(recallResponse)
  mockSearchDrugEvents.mockResolvedValue(drugResponse)
  window.history.replaceState(null, '', '?page=pharmacy-safety&q=Xanax')
})

test('renders a compact pharmacy dashboard with collapsed recall details', async () => {
  renderPharmacyPage()

  expect(
    await screen.findByRole('heading', { name: /Safety review for Xanax/i })
  ).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Matched official records/i })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /FAERS reporting summary/i })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Use these records to verify, not diagnose/i }))
    .toBeInTheDocument()
  expect(screen.getByText('SOMNOLENCE')).toBeInTheDocument()
  expect(screen.getByText(/Recall records retrieved/i)).toBeInTheDocument()
  expect(screen.queryByText(/Data lenses/i)).not.toBeInTheDocument()

  const productSummary = screen.getByTitle(longProductName)
  expect(productSummary.textContent).toMatch(/\.\.\.$/)
  expect(productSummary.closest('details')).not.toHaveAttribute('open')
})

test('loads the selected recall sort once', async () => {
  const user = userEvent.setup()

  renderPharmacyPage()

  expect(screen.getByRole('button', { name: 'Priority' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  expect(screen.getByRole('button', { name: 'Latest' })).toHaveAttribute(
    'aria-pressed',
    'false',
  )

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('Xanax', 8, 'score')
  })

  await user.click(screen.getByRole('button', { name: 'Latest' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('Xanax', 8, 'latest')
  })

  expect(screen.getByRole('button', { name: 'Priority' })).toHaveAttribute(
    'aria-pressed',
    'false',
  )
  expect(screen.getByRole('button', { name: 'Latest' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  expect(mockSearchRecalls).toHaveBeenCalledTimes(2)
})

test('empty input falls back to the submitted Pharmacy query', async () => {
  const user = userEvent.setup()
  renderPharmacyPage()

  await screen.findByRole('heading', { name: /Safety review for Xanax/i })
  await user.clear(screen.getByLabelText(/Search pharmacy records/i))
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledTimes(2)
  })

  expect(mockSearchRecalls).toHaveBeenLastCalledWith('Xanax', 8, 'score')
  expect(
    screen.queryByText(/Enter a drug, brand, active ingredient, or product wording/i),
  ).not.toBeInTheDocument()
})

test('spaces-only input falls back to the submitted Pharmacy query', async () => {
  const user = userEvent.setup()
  renderPharmacyPage()

  await screen.findByRole('heading', { name: /Safety review for Xanax/i })
  const input = screen.getByLabelText(/Search pharmacy records/i)
  await user.clear(input)
  await user.type(input, '   ')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchDrugEvents).toHaveBeenCalledTimes(2)
  })

  expect(mockSearchDrugEvents).toHaveBeenLastCalledWith('Xanax', 8)
})

test.each(['', '   '])(
  'shows quiet guidance for empty Pharmacy input without a current query: %j',
  async (value) => {
    const user = userEvent.setup()
    window.history.replaceState(null, '', '?page=pharmacy-safety')
    renderPharmacyPage('')

    const input = screen.getByLabelText(/Search pharmacy records/i)
    if (value) await user.type(input, value)
    await user.click(screen.getByRole('button', { name: 'Search' }))

    expect(
      screen.getByText(
        /Enter a drug, brand, active ingredient, or product wording/i,
      ),
    ).toBeInTheDocument()
    expect(mockSearchRecalls).not.toHaveBeenCalled()
    expect(mockSearchDrugEvents).not.toHaveBeenCalled()
  },
)

test('sort uses the submitted query even when the input is empty', async () => {
  const user = userEvent.setup()
  renderPharmacyPage()

  await screen.findByRole('heading', { name: /Safety review for Xanax/i })
  await user.clear(screen.getByLabelText(/Search pharmacy records/i))
  await user.click(screen.getByRole('button', { name: 'Latest' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenLastCalledWith('Xanax', 8, 'latest')
  })
})

test('example search clears previous empty-search guidance', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=pharmacy-safety')
  renderPharmacyPage('')

  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(screen.getByRole('status')).toHaveTextContent(
    /Enter a drug, brand, active ingredient, or product wording/i,
  )

  await user.click(screen.getByRole('button', { name: 'Metformin' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('Metformin', 8, 'score')
  })
  expect(
    screen.queryByText(/Enter a drug, brand, active ingredient, or product wording/i),
  ).not.toBeInTheDocument()
})

test.each([
  ['chicken', 'Food & Supplement Safety', 'food-safety'],
  ['sunscreen', 'Cosmetic Safety', 'cosmetic-safety'],
] as const)(
  'suggests %s searches use the correct safety page',
  async (query, label, page) => {
    const user = userEvent.setup()
    window.history.replaceState(null, '', '?page=pharmacy-safety')
    renderPharmacyPage('')

    await user.type(screen.getByLabelText(/Search pharmacy records/i), query)
    await user.click(screen.getByRole('button', { name: 'Search' }))

    const suggestion = await screen.findByText(
      new RegExp(`This looks more like a ${label} search`, 'i'),
    )
    const suggestionBox = suggestion.closest('.safety-route-suggestion')
    const examples = screen.getByLabelText('Example pharmacy searches')
    expect(suggestion.closest('.pharmacy-overview')).toBeInTheDocument()
    expect(
      suggestionBox!.compareDocumentPosition(examples) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).not.toBe(0)

    await user.click(screen.getByRole('button', { name: `Open ${label}` }))
    expect(mockGoToPage).toHaveBeenCalledWith(page, query)
  },
)

test('shows zero-result spelling guidance and runs the hardcoded typo correction', async () => {
  const user = userEvent.setup()
  mockSearchRecalls.mockResolvedValue(emptyRecallResponse)
  mockSearchDrugEvents.mockResolvedValue(emptyDrugResponse)
  window.history.replaceState(null, '', '?page=pharmacy-safety&q=metforimn')

  renderPharmacyPage('metforimn')

  expect(
    await screen.findByText(/No public records returned for this exact search/i),
  ).toBeInTheDocument()

  const suggestion = screen.getByText(/Spelling suggestion: did you mean/i)
  const suggestionBox = suggestion.closest('.pharmacy-typo-suggestion')
  const examples = screen.getByLabelText('Example pharmacy searches')
  expect(suggestionBox).toBeInTheDocument()
  expect(
    suggestionBox!.compareDocumentPosition(examples) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).not.toBe(0)
  expect(screen.queryByText('52/100')).not.toBeInTheDocument()
  expect(screen.getAllByText('No returned reports')).not.toHaveLength(0)
  expect(screen.getByText('Not assessable')).toBeInTheDocument()
  expect(screen.queryByText('Moderate')).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Use Metformin/i }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenLastCalledWith('Metformin', 8, 'score')
  })
  expect(new URLSearchParams(window.location.search).get('q')).toBe('Metformin')
})

test('wrong-category zero results show one focused route suggestion', async () => {
  const user = userEvent.setup()
  mockSearchRecalls.mockResolvedValue(emptyRecallResponse)
  mockSearchDrugEvents.mockResolvedValue(emptyDrugResponse)
  window.history.replaceState(null, '', '?page=pharmacy-safety')
  renderPharmacyPage('')

  await user.type(screen.getByLabelText(/Search pharmacy records/i), 'Chicken')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    await screen.findByText(/This looks more like a Food & Supplement Safety search/i),
  ).toBeInTheDocument()
  expect(
    screen.getByText(/This looks better suited for Food & Supplement Safety/i),
  ).toBeInTheDocument()
  expect(
    screen.queryByText(/No public records returned for this exact search/i),
  ).not.toBeInTheDocument()
})

test('normalizes whitespace and skips a completed equivalent query', async () => {
  const user = userEvent.setup()
  renderPharmacyPage()

  await screen.findByRole('heading', { name: /Safety review for Xanax/i })
  const input = screen.getByLabelText(/Search pharmacy records/i)
  await user.clear(input)
  await user.type(input, '   xanax   ')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(mockSearchRecalls).toHaveBeenCalledTimes(1)
  expect(input).toHaveValue('xanax')
})

test('reacts safely when the route initial query changes', async () => {
  const { rerender } = renderPharmacyPage()

  await screen.findByRole('heading', { name: /Safety review for Xanax/i })

  window.history.replaceState(null, '', '?page=pharmacy-safety&q=Metformin%20XR')
  rerender(
    <PharmacySafetyPage initialQuery="  Metformin   XR  " goToPage={mockGoToPage} />,
  )

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenLastCalledWith('Metformin XR', 8, 'score')
  })
  expect(
    screen.getByRole('heading', { name: /Safety review for Metformin XR/i }),
  ).toBeInTheDocument()
})

test('shows partial Pharmacy results when one public source fails', async () => {
  mockSearchRecalls.mockRejectedValueOnce(new Error('Recall source unavailable'))
  renderPharmacyPage()

  expect(
    await screen.findByText(/Some public sources were unavailable/i),
  ).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /FAERS reporting summary/i })).toBeInTheDocument()
  expect(screen.getByText('SOMNOLENCE')).toBeInTheDocument()
  expect(screen.getByText('Unavailable')).toBeInTheDocument()
})

test('clears a source error after a later successful search', async () => {
  const user = userEvent.setup()
  mockSearchRecalls.mockRejectedValueOnce(new Error('Recall source unavailable'))
  mockSearchDrugEvents.mockRejectedValueOnce(new Error('Drug source unavailable'))
  renderPharmacyPage()

  expect(
    await screen.findByText(/Unable to load public records/i),
  ).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Metformin' }))

  await waitFor(() => {
    expect(screen.queryByText(/Unable to load public records/i)).not.toBeInTheDocument()
  })
  expect(mockSearchRecalls).toHaveBeenLastCalledWith('Metformin', 8, 'score')
})
