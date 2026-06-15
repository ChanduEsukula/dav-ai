import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  searchCosmeticEvents,
  type CosmeticEventSearchResponse,
} from '../api/cosmeticEvents'
import CosmeticSignal from './CosmeticSignal'

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

const baseResponse: CosmeticEventSearchResponse = {
  query: 'Sunscreen',
  count: 1,
  limit: 10,
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
    record_count: 1,
    transform_version: 'cosmetic-event-v1',
    source_snapshot_status: null,
    source_pull_id: null,
    source_payload_hash: null,
  },
  signal_score: {
    score: 42,
    label: 'Moderate',
    data_confidence: 'Limited',
    top_reaction_concentration: 50,
    review_priority: 'Watch',
    score_version: 'cosmetic-signal-v1',
    limitations: ['Reports do not prove causation.'],
  },
  top_reactions: [{ reaction: 'RASH', count: 1 }],
  records: [
    {
      report_number: 'CAERS-FALLBACK-002',
      report_date: '20260601',
      serious: 'No',
      outcomes: ['Other'],
      reactions: ['RASH'],
      products: [],
    },
  ],
}

const emptyResponse: CosmeticEventSearchResponse = {
  ...baseResponse,
  count: 0,
  records: [],
  top_reactions: [],
  audit: {
    ...baseResponse.audit,
    record_count: 0,
  },
  signal_score: {
    ...baseResponse.signal_score,
    score: 0,
    label: 'No signal',
    top_reaction_concentration: 0,
  },
}

beforeEach(() => {
  mockSearchCosmeticEvents.mockReset()
  mockSearchCosmeticEvents.mockResolvedValue(baseResponse)
})

test('normalizes CosmeticSignal whitespace and uses the report number fallback', async () => {
  const user = userEvent.setup()
  render(<CosmeticSignal />)

  const input = screen.getByLabelText(/Cosmetic brand, product, reaction, or outcome/i)
  await user.type(input, '  Mineral   sunscreen  ')
  await user.click(screen.getByRole('button', { name: 'Analyze cosmetics' }))

  await waitFor(() => {
    expect(mockSearchCosmeticEvents).toHaveBeenCalledWith('Mineral sunscreen', 10)
  })
  expect(input).toHaveValue('Mineral sunscreen')
  expect(
    await screen.findByRole('heading', { name: 'Cosmetic report CAERS-FALLBACK-002' }),
  ).toBeInTheDocument()
  expect(screen.queryByText('Unnamed product')).not.toBeInTheDocument()
})

test('does not present a zero-result CosmeticSignal response as a 0/100 safety score', async () => {
  const user = userEvent.setup()
  mockSearchCosmeticEvents.mockResolvedValue(emptyResponse)
  render(<CosmeticSignal />)

  await user.type(
    screen.getByLabelText(/Cosmetic brand, product, reaction, or outcome/i),
    'Unknown cream',
  )
  await user.click(screen.getByRole('button', { name: 'Analyze cosmetics' }))

  expect(await screen.findByRole('heading', { name: 'No reports' })).toBeInTheDocument()
  expect(screen.queryByText(/0\s*\/\s*100/i)).not.toBeInTheDocument()
  expect(screen.getByText(/A no-match result does not prove safety or harm/i)).toBeInTheDocument()
})
