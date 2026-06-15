import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  searchEverydaySafety,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import FoodRadar from './FoodRadar'

vi.mock('../api/everydaySafety', async () => {
  const actual = await vi.importActual<typeof import('../api/everydaySafety')>(
    '../api/everydaySafety',
  )

  return {
    ...actual,
    searchEverydaySafety: vi.fn(),
  }
})

const mockSearchEverydaySafety = vi.mocked(searchEverydaySafety)

const foodResponse: EverydaySafetySearchResponse = {
  query: 'Chicken',
  category: 'food_supplement',
  category_label: 'Food & Supplements',
  count: 1,
  limit: 5,
  source_name: 'FDA Food Enforcement + USDA FSIS',
  endpoint: '/api/v1/everyday-safety/search',
  retrieval_timestamp: '2026-06-12T12:00:00Z',
  score_version: 'everyday-safety-score-v1',
  search_strategy_used: 'exact_then_broad',
  sources_checked: [
    {
      source_id: 'openfda-food-enforcement',
      source_name: 'openFDA Food Enforcement API',
      source_type: 'FDA_FOOD_ENFORCEMENT',
      endpoint: 'https://api.fda.gov/food/enforcement.json',
      upstream_status: 'success',
      record_count: 1,
    },
  ],
  public_data_disclaimer: 'Public records only.',
  limitations: ['No result is a safety guarantee.'],
  audit: {
    audit_id: 'food-audit',
    source_id: 'everyday-safety',
    module: 'FoodRadar',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'food-transform-v1',
    source_snapshot_status: null,
    source_pull_id: null,
    source_payload_hash: null,
  },
  results: [
    {
      record_id: 'FDA-001',
      recall_number: 'F-1001-2026',
      product_description: null,
      reason_for_recall: 'Undeclared allergen',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260520',
      report_date: null,
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Foods',
      product_quantity: '800 cases',
      code_info: 'Lot 55A',
      source_type: 'FDA_FOOD_ENFORCEMENT',
      search_strategy_used: 'exact_then_broad',
      risk_score: {
        score: 62,
        label: 'Moderate',
        components: {
          classification_score: 25,
          status_score: 15,
          recency_score: 12,
          scope_score: 10,
        },
        score_version: 'everyday-safety-score-v1',
      },
      source: {
        name: 'openFDA Food Enforcement API',
        endpoint: 'https://api.fda.gov/food/enforcement.json',
        retrieval_timestamp: '2026-06-12T12:00:00Z',
      },
    },
  ],
}

beforeEach(() => {
  mockSearchEverydaySafety.mockReset()
  mockSearchEverydaySafety.mockResolvedValue(foodResponse)
})

test('uses review-priority sort semantics and a useful FoodRadar title fallback', async () => {
  const user = userEvent.setup()
  render(<FoodRadar />)

  await user.type(screen.getByLabelText(/Food, supplement, or product/i), 'Chicken')
  await user.click(screen.getByRole('button', { name: 'Check FoodRadar' }))

  const fallbackTitle = await screen.findByRole('heading', {
    name: 'Recall F-1001-2026',
  })
  expect(fallbackTitle).toHaveAttribute('title', 'Recall F-1001-2026')
  expect(screen.getByText('Moderate review signal')).toBeInTheDocument()

  const priorityButton = screen.getByRole('button', {
    name: 'Highest review priority',
  })
  const latestButton = screen.getByRole('button', { name: 'Latest recall' })
  expect(priorityButton).toHaveAttribute('aria-pressed', 'true')
  expect(latestButton).toHaveAttribute('aria-pressed', 'false')

  await user.click(latestButton)

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenLastCalledWith(
      'Chicken',
      5,
      'food_supplement',
      'latest',
    )
  })
  expect(priorityButton).toHaveAttribute('aria-pressed', 'false')
  expect(latestButton).toHaveAttribute('aria-pressed', 'true')
})
