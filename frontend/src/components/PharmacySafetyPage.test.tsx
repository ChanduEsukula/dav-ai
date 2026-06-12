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

beforeEach(() => {
  mockSearchRecalls.mockReset()
  mockSearchDrugEvents.mockReset()
  mockSearchRecalls.mockResolvedValue(recallResponse)
  mockSearchDrugEvents.mockResolvedValue(drugResponse)
  window.history.replaceState(null, '', '?page=pharmacy-safety&q=Xanax')
})

test('renders a compact pharmacy dashboard with collapsed recall details', async () => {
  render(<PharmacySafetyPage initialQuery="Xanax" />)

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

  render(<PharmacySafetyPage initialQuery="Xanax" />)

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('Xanax', 8, 'score')
  })

  await user.click(screen.getByRole('button', { name: 'Latest' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('Xanax', 8, 'latest')
  })

  expect(mockSearchRecalls).toHaveBeenCalledTimes(2)
})
