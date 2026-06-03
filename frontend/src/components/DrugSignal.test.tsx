import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DrugSignal from './DrugSignal'
import { searchDrugEvents } from '../api/drugEvents'
import type { DrugEventSearchResponse } from '../api/drugEvents'

vi.mock('../api/drugEvents', async () => {
  const actual = await vi.importActual<typeof import('../api/drugEvents')>(
    '../api/drugEvents'
  )

  return {
    ...actual,
    searchDrugEvents: vi.fn(),
  }
})

const mockSearchDrugEvents = vi.mocked(searchDrugEvents)

const mockResponse: DrugEventSearchResponse = {
  query: 'metformin',
  count: 2,
  limit: 10,
  source_name: 'openFDA Drug Event API',
  endpoint: 'https://api.fda.gov/drug/event.json',
  retrieval_timestamp: '2026-05-03T12:00:00Z',
  medical_disclaimer:
    'Dav AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.',
  faers_disclaimer:
    'FAERS reports are safety signals only and do not prove causation.',
  audit: {
    audit_id: 'drug-audit-123',
    source_id: 'openfda-drug-event',
    module: 'DrugSignal',
    upstream_status: 'success',
    record_count: 2,
    transform_version: 'drug-event-transform-v1',
  },
  intelligence_score: {
    score: 57,
    label: 'Moderate',
    data_confidence: 'Limited',
    top_reaction_concentration: 66.67,
    review_priority: 'Watch',
    score_version: 'drug-signal-intelligence-v0.1',
    limitations: [
      'FAERS reports are safety signals only and do not prove causation.',
      'Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.',
    ],
  },
  reaction_categories: [
    {
      category: 'Gastrointestinal',
      count: 12,
      reactions: ['NAUSEA'],
    },
    {
      category: 'Neurological',
      count: 6,
      reactions: ['HEADACHE'],
    },
  ],
  reaction_classifier_version: 'reaction-classifier-v0.1',
  trend_snapshot: {
    label: 'Increased',
    current_record_count: 2,
    previous_record_count: 1,
    previous_audit_id: 'previous-audit-123',
    previous_created_at: '2026-05-02T12:00:00Z',
    explanation: 'Compared with the most recent stored DrugSignal audit event for this query.',
    limitation: 'Trend is based only on stored public-data searches in Dav AI, not all FDA activity.',
    trend_version: 'drug-signal-trend-v0.1',
  },
  top_reactions: [
    {
      reaction: 'NAUSEA',
      count: 12,
    },
    {
      reaction: 'HEADACHE',
      count: 6,
    },
  ],
}

beforeEach(() => {
  mockSearchDrugEvents.mockReset()
})

test('renders DrugSignal search input and button', () => {
  render(<DrugSignal />)

  expect(
    screen.getByRole('heading', {
      name: /Explore public FAERS adverse-event reporting patterns/i,
    })
  ).toBeInTheDocument()

  expect(screen.getByPlaceholderText(/Search FAERS reports/i)).toBeInTheDocument()

  expect(screen.getByRole('button', { name: /Analyze/i })).toBeInTheDocument()

  expect(screen.getByText(/do not prove causation/i)).toBeInTheDocument()
})

test('shows validation error for empty search', async () => {
  const user = userEvent.setup()

  render(<DrugSignal />)

  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(
    screen.getByText(/Enter a drug or medicinal product name/i)
  ).toBeInTheDocument()

  expect(mockSearchDrugEvents).not.toHaveBeenCalled()
})

test('shows loading state during search', async () => {
  const user = userEvent.setup()

  mockSearchDrugEvents.mockImplementation(
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve(mockResponse), 50)
      })
  )

  render(<DrugSignal />)

  await user.type(screen.getByPlaceholderText(/Search FAERS reports/i), 'metformin')
  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(screen.getByRole('button', { name: /Checking public data/i })).toBeDisabled()

  await waitFor(() => {
    expect(mockSearchDrugEvents).toHaveBeenCalledWith('metformin', 10, 'reports')
  })
})

test('shows successful reaction results with source, disclaimers, and briefing information', async () => {
  const user = userEvent.setup()

  mockSearchDrugEvents.mockResolvedValue(mockResponse)

  render(<DrugSignal />)

  await user.type(screen.getByPlaceholderText(/Search FAERS reports/i), 'metformin')
  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(await screen.findByText(/2 FAERS records reviewed/i)).toBeInTheDocument()

  expect(
    screen.getAllByText(/openFDA Drug Event API/i).length
  ).toBeGreaterThan(0)

  expect(
    screen.getByRole('heading', { name: /Top reported reactions/i })
  ).toBeInTheDocument()

  expect(screen.getAllByText(/NAUSEA/i).length).toBeGreaterThan(0)
  expect(screen.getAllByText('12').length).toBeGreaterThan(0)
  expect(screen.getAllByText(/HEADACHE/i).length).toBeGreaterThan(0)
  expect(screen.getAllByText('6').length).toBeGreaterThan(0)

  expect(
    screen.getAllByText(/FAERS reports are safety signals only/i).length
  ).toBeGreaterThan(0)

  expect(
    screen.getAllByText(/not medical advice, diagnosis, or treatment/i).length
  ).toBeGreaterThan(0)

  expect(screen.getAllByText(/drug-audit-123/i).length).toBeGreaterThan(0)
  expect(screen.getAllByText(/DrugSignal/i).length).toBeGreaterThan(0)

  expect(screen.getAllByText(/DrugSignal Intelligence/i).length).toBeGreaterThan(0)
  expect(screen.getByText(/57 \/ 100/i)).toBeInTheDocument()
  expect(screen.getByText(/Transparent signal score/i)).toBeInTheDocument()
  expect(screen.getByText('Moderate')).toBeInTheDocument()
  expect(screen.getByText('Watch')).toBeInTheDocument()
  expect(screen.getByText('Limited')).toBeInTheDocument()
  expect(screen.getByText('66.67%')).toBeInTheDocument()
  expect(screen.getAllByText('drug-signal-intelligence-v0.1').length).toBeGreaterThan(0)
  expect(screen.getAllByText(/not clinical incidence rates/i).length).toBeGreaterThan(0)

  expect(screen.getAllByText(/Reaction Classification/i).length).toBeGreaterThan(0)
  expect(screen.getByRole('heading', { name: /Reaction categories/i })).toBeInTheDocument()
  expect(screen.getByText(/Rule-based NLP-style grouping/i)).toBeInTheDocument()
  expect(screen.getByText('Gastrointestinal')).toBeInTheDocument()
  expect(screen.getByText('Neurological')).toBeInTheDocument()
  expect(screen.getAllByText(/reaction-classifier-v0.1/i).length).toBeGreaterThan(0)

  expect(screen.getByText(/DrugSignal Trend Snapshot/i)).toBeInTheDocument()
  expect(screen.getByText('Increased')).toBeInTheDocument()
  expect(screen.getByText(/Current records/i)).toBeInTheDocument()
  expect(screen.getByText(/Previous records/i)).toBeInTheDocument()
  expect(screen.getByText('previous-audit-123')).toBeInTheDocument()
  expect(screen.getByText(/drug-signal-trend-v0.1/i)).toBeInTheDocument()
  expect(screen.getByText(/stored public-data searches/i)).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Consumer briefing/i })
  ).toBeInTheDocument()

  expect(screen.getByText(/Safety Briefing Engine v2/i)).toBeInTheDocument()

  expect(screen.getByLabelText(/Briefing role/i)).toBeInTheDocument()

  expect(
    screen.getByText(/These are adverse-event reporting patterns only/i)
  ).toBeInTheDocument()

  expect(screen.getByText(/DrugSignal Intelligence score: 57\/100 Moderate/i)).toBeInTheDocument()
  expect(screen.getByText(/Leading reaction category: Gastrointestinal/i)).toBeInTheDocument()
  expect(screen.getByText(/Review score version: drug-signal-intelligence-v0.1/i)).toBeInTheDocument()
  expect(screen.getByText(/Review reaction classifier version: reaction-classifier-v0.1/i)).toBeInTheDocument()
})

test('shows no-results state with safety language', async () => {
  const user = userEvent.setup()

  mockSearchDrugEvents.mockResolvedValue({
    ...mockResponse,
    count: 0,
    audit: {
      ...mockResponse.audit,
      record_count: 0,
    },
    intelligence_score: {
      ...mockResponse.intelligence_score,
      score: 10,
      label: 'Low',
      data_confidence: 'Limited',
      top_reaction_concentration: 0,
      review_priority: 'Low',
    },
    reaction_categories: [],
    trend_snapshot: {
      ...mockResponse.trend_snapshot,
      label: 'Insufficient history',
      current_record_count: 0,
      previous_record_count: null,
      previous_audit_id: null,
      previous_created_at: null,
      explanation: 'No previous stored DrugSignal audit event was available for this query.',
    },
    top_reactions: [],
  })

  render(<DrugSignal />)

  await user.type(screen.getByPlaceholderText(/Search FAERS reports/i), 'unknown drug')
  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(
    await screen.findByRole('heading', {
      name: /No FAERS drug-event records matched this search/i,
    })
  ).toBeInTheDocument()

  expect(
    screen.getByText(/This does not prove the drug is safe or unsafe/i)
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Consumer briefing/i })
  ).toBeInTheDocument()

  expect(screen.getByText(/Safety Briefing Engine v2/i)).toBeInTheDocument()

  expect(screen.getByLabelText(/Briefing role/i)).toBeInTheDocument()
})

test('shows error message when API call fails', async () => {
  const user = userEvent.setup()

  mockSearchDrugEvents.mockRejectedValue(new Error('Network error'))

  render(<DrugSignal />)

  await user.type(screen.getByPlaceholderText(/Search FAERS reports/i), 'metformin')
  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(
    await screen.findByText(/Unable to load drug event data/i)
  ).toBeInTheDocument()
})

test('runs search when Enter key is pressed', async () => {
  const user = userEvent.setup()

  mockSearchDrugEvents.mockResolvedValue(mockResponse)

  render(<DrugSignal />)

  await user.type(
    screen.getByPlaceholderText(/Search FAERS reports/i),
    'metformin{enter}'
  )

  await waitFor(() => {
    expect(mockSearchDrugEvents).toHaveBeenCalledWith('metformin', 10, 'reports')
  })
})