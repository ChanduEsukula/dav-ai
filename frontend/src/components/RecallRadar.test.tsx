import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RecallRadar from './RecallRadar'
import type { RecallSearchResponse } from '../api/recalls'

const mockResponse: RecallSearchResponse = {
  query: 'eye drops',
  count: 1,
  limit: 5,
  source_name: 'openFDA Drug Enforcement API',
  endpoint: 'https://api.fda.gov/drug/enforcement.json',
  retrieval_timestamp: '2026-05-03T12:00:00Z',
  score_version: 'recall-score-v1',
  medical_disclaimer:
    'MedSignal AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.',
  audit: {
    audit_id: 'audit-123',
    source_id: 'openfda-drug-enforcement',
    module: 'RecallRadar',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'recall-transform-v1',
  },
  results: [
    {
      recall_number: 'D-1234-2026',
      product_description: 'Example Eye Drops',
      reason_for_recall: 'Potential microbial contamination',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260420',
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Pharma',
      risk_score: {
        score: 72,
        label: 'High',
        components: {
          classification_score: 30,
          status_score: 20,
          recency_score: 12,
          scope_score: 10,
        },
        score_version: 'recall-score-v1',
      },
      source: {
        name: 'openFDA Drug Enforcement API',
        endpoint: 'https://api.fda.gov/drug/enforcement.json',
        retrieval_timestamp: '2026-05-03T12:00:00Z',
      },
    },
  ],
}

function renderRecallRadar(
  overrides: Partial<{
    query: string
    data: RecallSearchResponse | null
    loading: boolean
    error: string
    setQuery: (query: string) => void
    handleSearch: () => void
  }> = {}
) {
  const props = {
    query: '',
    setQuery: vi.fn(),
    data: null,
    loading: false,
    error: '',
    handleSearch: vi.fn(),
    ...overrides,
  }

  render(<RecallRadar {...props} />)

  return props
}

test('renders RecallRadar search input and button', () => {
  renderRecallRadar()

  expect(
    screen.getByRole('heading', { name: /Search public FDA recall signals/i })
  ).toBeInTheDocument()

  expect(screen.getByPlaceholderText(/Search recalls/i)).toBeInTheDocument()

  expect(screen.getByRole('button', { name: /Analyze/i })).toBeInTheDocument()
})

test('calls setQuery when the user types', async () => {
  const user = userEvent.setup()
  const setQuery = vi.fn()

  renderRecallRadar({ setQuery })

  await user.type(screen.getByPlaceholderText(/Search recalls/i), 'eye drops')

  expect(setQuery).toHaveBeenCalled()
})

test('calls handleSearch when Analyze is clicked', async () => {
  const user = userEvent.setup()
  const handleSearch = vi.fn()

  renderRecallRadar({ handleSearch })

  await user.click(screen.getByRole('button', { name: /Analyze/i }))

  expect(handleSearch).toHaveBeenCalledTimes(1)
})

test('shows loading state and disables button', () => {
  renderRecallRadar({ loading: true })

  const button = screen.getByRole('button', { name: /Analyzing/i })

  expect(button).toBeDisabled()
})

test('shows error message', () => {
  renderRecallRadar({ error: 'Unable to reach the backend API.' })

  expect(
    screen.getByText(/Unable to reach the backend API/i)
  ).toBeInTheDocument()
})

test('shows no-results safety message', () => {
  renderRecallRadar({
    query: 'unknown product',
    data: {
      ...mockResponse,
      query: 'unknown product',
      count: 0,
      audit: {
        ...mockResponse.audit,
        record_count: 0,
      },
      results: [],
    },
  })

  expect(
    screen.getByRole('heading', {
      name: /No FDA recall records matched this search/i,
    })
  ).toBeInTheDocument()

  expect(
    screen.getByText(/This does not prove the product is safe or unsafe/i)
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Consumer briefing/i })
  ).toBeInTheDocument()

  expect(screen.getByText(/Safety Briefing Engine v1/i)).toBeInTheDocument()

  expect(screen.getByLabelText(/Briefing role/i)).toBeInTheDocument()
})

test('shows successful recall result with source, audit, and briefing information', () => {
  renderRecallRadar({ query: 'eye drops', data: mockResponse })

  expect(screen.getByText(/1 records matched/i)).toBeInTheDocument()

  expect(
    screen.getAllByText(/openFDA Drug Enforcement API/i).length
  ).toBeGreaterThan(0)

  expect(
    screen.getByRole('heading', { name: /Example Eye Drops/i })
  ).toBeInTheDocument()

  expect(
    screen.getAllByText(/Potential microbial contamination/i).length
  ).toBeGreaterThan(0)

  expect(screen.getAllByText(/High signal/i).length).toBeGreaterThan(0)
  expect(screen.getByText('72')).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Consumer briefing/i })
  ).toBeInTheDocument()

  expect(screen.getByText(/Safety Briefing Engine v1/i)).toBeInTheDocument()

  expect(screen.getByLabelText(/Briefing role/i)).toBeInTheDocument()

  expect(
    screen.getByText(/This briefing summarizes public safety-signal information/i)
  ).toBeInTheDocument()

  expect(
    screen.getByText(/Suggested review checklist/i)
  ).toBeInTheDocument()

  expect(
    screen.getAllByText(/audit-123/i).length
  ).toBeGreaterThan(0)

  expect(
    screen.getAllByText(
      /MedSignal AI provides public-data safety intelligence only/i
    ).length
  ).toBeGreaterThan(0)
})