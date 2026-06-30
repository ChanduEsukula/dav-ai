import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  searchEverydaySafety,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import FoodSafetyPage from './FoodSafetyPage'

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
const mockGoToPage = vi.fn()

const chickenProduct =
  'Ready-to-eat chicken salad in 12-ounce packages with establishment and label details'

const foodResponse: EverydaySafetySearchResponse = {
  query: 'Chicken',
  category: 'food_supplement',
  category_label: 'Food & Supplements',
  count: 2,
  limit: 8,
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
    {
      source_id: 'usda-fsis-recalls',
      source_name: 'USDA FSIS Recall Records',
      source_type: 'USDA_FSIS_RECALL',
      endpoint: 'https://www.fsis.usda.gov/recalls',
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
    record_count: 2,
    transform_version: 'food-transform-v1',
    source_snapshot_status: null,
    source_pull_id: null,
    source_payload_hash: null,
  },
  results: [
    {
      record_id: 'FSIS-001',
      recall_number: '023-2026',
      product_description: chickenProduct,
      reason_for_recall: 'Possible contamination',
      classification: 'Class I',
      status: 'Active',
      recall_initiation_date: '20260601',
      report_date: '20260602',
      distribution_pattern: 'Nationwide',
      recalling_firm: 'Example Foods',
      product_quantity: '2,400 pounds',
      code_info: 'Use by 06/20/2026; lot C26',
      source_type: 'USDA_FSIS_RECALL',
      search_strategy_used: 'exact_then_broad',
      risk_score: {
        score: 86,
        label: 'High',
        components: {
          classification_score: 35,
          status_score: 20,
          recency_score: 16,
          scope_score: 15,
        },
        score_version: 'everyday-safety-score-v1',
      },
      source: {
        name: 'USDA FSIS Recall Records',
        endpoint: 'https://www.fsis.usda.gov/recalls/023-2026',
        retrieval_timestamp: '2026-06-12T12:00:00Z',
      },
    },
    {
      record_id: 'FDA-002',
      recall_number: 'F-1001-2026',
      product_description: 'Frozen chicken and vegetable meal, 16-ounce package',
      reason_for_recall: 'Undeclared allergen',
      classification: 'Class II',
      status: 'Ongoing',
      recall_initiation_date: '20260520',
      report_date: null,
      distribution_pattern: 'Texas and Oklahoma',
      recalling_firm: 'Sample Kitchen',
      product_quantity: '800 cases',
      code_info: 'UPC 000111222; lot 55A',
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

const emptyFoodResponse: EverydaySafetySearchResponse = {
  ...foodResponse,
  count: 0,
  results: [],
  sources_checked: foodResponse.sources_checked.map((source) => ({
    ...source,
    record_count: 0,
    upstream_status: 'empty',
  })),
  audit: {
    ...foodResponse.audit,
    record_count: 0,
  },
}

const normalizedNoticeFoodResponse: EverydaySafetySearchResponse = {
  ...emptyFoodResponse,
  query: 'Pepperoni',
  count: 1,
  sources_checked: [
    ...emptyFoodResponse.sources_checked,
    {
      source_id: 'fda-public-notices',
      source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
      source_type: 'FDA_NORMALIZED_PUBLIC_NOTICE',
      endpoint: 'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
      source_kind: 'normalized_public_notice',
      record_type: 'normalized official public notice',
      upstream_status: 'success',
      record_count: 1,
    },
  ],
  results: [
    {
      record_id: 'pepperoni-notice',
      recall_number: null,
      product_description: 'Pepperoni Rolls',
      reason_for_recall: 'Pepperoni Rolls were recalled due to undeclared milk.',
      classification: null,
      status: null,
      recall_initiation_date: '20260610',
      report_date: '20260610',
      distribution_pattern: null,
      recalling_firm: 'Fry Pie Factory LLC',
      product_quantity: null,
      code_info: null,
      source_type: 'FDA_NORMALIZED_PUBLIC_NOTICE',
      source_kind: 'normalized_public_notice',
      source_record_type: 'normalized official public notice',
      remedy: 'Consumers should return the product for a refund.',
      official_url: 'https://www.fda.gov/safety/notices/pepperoni-rolls',
      affected_models: [],
      affected_lots: [],
      extraction_confidence: 'high',
      source_text_excerpt: 'UNIQUE_INTERNAL_FDA_PAGE_TEXT_DO_NOT_RENDER',
      search_strategy_used: 'intent_brand_v1',
      risk_score: {
        score: 32,
        label: 'Moderate',
        components: {
          classification_score: 5,
          status_score: 5,
          recency_score: 17,
          scope_score: 5,
        },
        score_version: 'everyday-safety-score-v1',
      },
      source: {
        name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
        endpoint: 'https://www.fda.gov/safety/notices/pepperoni-rolls',
        retrieval_timestamp: '2026-06-12T12:00:00Z',
        source_kind: 'normalized_public_notice',
        source_type: 'normalized official public notice',
      },
    },
  ],
}

function renderFoodPage(initialQuery = 'Chicken') {
  return render(
    <FoodSafetyPage
      initialQuery={initialQuery}
      goToPage={mockGoToPage}
    />,
  )
}

beforeEach(() => {
  mockGoToPage.mockReset()
  mockSearchEverydaySafety.mockReset()
  mockSearchEverydaySafety.mockResolvedValue(foodResponse)
  window.history.replaceState(null, '', '?page=food-safety&q=Chicken')
})

test('renders the FoodSignal dashboard and multiple records for Chicken', async () => {
  renderFoodPage()

  expect(
    await screen.findByRole('heading', { name: /Safety review for Chicken/i }),
  ).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Matched food records/i })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Public records checked/i })).toBeInTheDocument()
  expect(
    screen.getAllByText('Frozen chicken and vegetable meal, 16-ounce package'),
  ).toHaveLength(2)
  expect(screen.getByText(/Showing 2 of 2 returned records/i)).toBeInTheDocument()
  expect(screen.getAllByText('Live public API').length).toBeGreaterThan(0)
})

test('renders normalized FDA notices with concise fields and an official link', async () => {
  const user = userEvent.setup()
  mockSearchEverydaySafety.mockResolvedValue(normalizedNoticeFoodResponse)
  renderFoodPage('Pepperoni')

  expect(await screen.findByTitle('Pepperoni Rolls')).toBeInTheDocument()
  expect(screen.getAllByText('Normalized public notice').length).toBeGreaterThan(0)
  expect(screen.getAllByText('Live public page').length).toBeGreaterThan(0)
  await user.click(screen.getByTitle('Pepperoni Rolls'))

  expect(
    screen.getByText('Pepperoni Rolls were recalled due to undeclared milk.'),
  ).toBeInTheDocument()
  expect(
    screen.getByText('Consumers should return the product for a refund.'),
  ).toBeInTheDocument()
  expect(screen.getByText('high')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Open official record' })).toHaveAttribute(
    'href',
    'https://www.fda.gov/safety/notices/pepperoni-rolls',
  )
  expect(
    screen.queryByText('UNIQUE_INTERNAL_FDA_PAGE_TEXT_DO_NOT_RENDER'),
  ).not.toBeInTheDocument()
})

test('loads normalized Food records with the required category, limit, and priority sort', async () => {
  window.history.replaceState(null, '', '?page=food-safety&q=Chicken%20Salad')
  renderFoodPage('  Chicken   Salad  ')

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledWith(
      'Chicken Salad',
      8,
      'food_supplement',
      'score',
    )
  })
})

test('empty input falls back to the submitted Food query', async () => {
  const user = userEvent.setup()
  renderFoodPage()

  await screen.findByRole('heading', { name: /Safety review for Chicken/i })
  await user.clear(screen.getByLabelText(/Search food safety records/i))
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledTimes(2)
  })
  expect(mockSearchEverydaySafety).toHaveBeenLastCalledWith(
    'Chicken',
    8,
    'food_supplement',
    'score',
  )
})

test('spaces-only input falls back to the submitted Food query', async () => {
  const user = userEvent.setup()
  renderFoodPage()

  await screen.findByRole('heading', { name: /Safety review for Chicken/i })
  const input = screen.getByLabelText(/Search food safety records/i)
  await user.clear(input)
  await user.type(input, '   ')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledTimes(2)
  })
  expect(mockSearchEverydaySafety).toHaveBeenLastCalledWith(
    'Chicken',
    8,
    'food_supplement',
    'score',
  )
})

test('empty input with no submitted query shows quiet Food guidance', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=food-safety')
  renderFoodPage('')

  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    screen.getByText(
      /Enter a food, supplement, brand, ingredient, or product wording/i,
    ),
  ).toBeInTheDocument()
  expect(mockSearchEverydaySafety).not.toHaveBeenCalled()
})

test('an example chip runs a new search and clears empty-search guidance', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=food-safety')
  renderFoodPage('')

  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(screen.getByText(/Enter a food, supplement, brand/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Peanut butter' }))

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledWith(
      'Peanut butter',
      8,
      'food_supplement',
      'score',
    )
  })
  expect(screen.queryByText(/Enter a food, supplement, brand/i)).not.toBeInTheDocument()
})

test('Latest sort reloads the submitted query with latest ordering', async () => {
  const user = userEvent.setup()
  renderFoodPage()

  expect(screen.getByRole('button', { name: 'Priority' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await screen.findByRole('heading', { name: /Safety review for Chicken/i })
  await user.click(screen.getByRole('button', { name: 'Latest' }))

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenLastCalledWith(
      'Chicken',
      8,
      'food_supplement',
      'latest',
    )
  })
  expect(screen.getByRole('button', { name: 'Latest' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
})

test('a Xanax Food search suggests DrugSignal', async () => {
  const user = userEvent.setup()
  mockSearchEverydaySafety.mockResolvedValue(emptyFoodResponse)
  window.history.replaceState(null, '', '?page=food-safety')
  renderFoodPage('')

  await user.type(screen.getByLabelText(/Search food safety records/i), 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  const suggestion = await screen.findByText(
    /This looks more like a DrugSignal search/i,
  )
  const suggestionBox = suggestion.closest('.safety-route-suggestion')
  const examples = screen.getByLabelText('Example food safety searches')
  expect(suggestion.closest('.food-overview')).toBeInTheDocument()
  expect(
    suggestionBox!.compareDocumentPosition(examples) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).not.toBe(0)
  expect(screen.getByText(/This looks better suited for DrugSignal/i)).toBeInTheDocument()
  expect(
    screen.queryByText(/No public records returned for this exact search/i),
  ).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Open DrugSignal' }))
  expect(mockGoToPage).toHaveBeenCalledWith('pharmacy-safety', 'Xanax')
})

test('a Sunscreen Food search suggests Personal Care Signals', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '?page=food-safety')
  renderFoodPage('')

  await user.type(screen.getByLabelText(/Search food safety records/i), 'Sunscreen')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    await screen.findByText(/This looks more like a Personal Care Signals search/i),
  ).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Open Personal Care Signals' }))
  expect(mockGoToPage).toHaveBeenCalledWith('cosmetic-safety', 'Sunscreen')
})

test('zero records show calm guidance without claiming the product is safe', async () => {
  mockSearchEverydaySafety.mockResolvedValue(emptyFoodResponse)
  renderFoodPage('Unknown snack')

  expect(
    await screen.findByText(/No public records returned for this exact search/i),
  ).toBeInTheDocument()
  expect(
    screen.getAllByText(/No result does not prove a food or supplement is safe/i),
  ).not.toHaveLength(0)
  expect(screen.queryByText(/This product is safe/i)).not.toBeInTheDocument()
})

test('normalizes strawberries and preserves the original Food query', async () => {
  window.history.replaceState(null, '', '?page=food-safety&q=strawberries')
  renderFoodPage('strawberries')

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledWith(
      'strawberry',
      8,
      'food_supplement',
      'score',
    )
  })
  expect(
    screen.getByText(
      /Showing results for 'strawberry' based on your search 'strawberries'/i,
    ),
  ).toBeInTheDocument()
  expect(screen.getByLabelText(/Search food safety records/i)).toHaveValue('strawberries')
  expect(new URLSearchParams(window.location.search).get('q')).toBe('strawberry')
  expect(new URLSearchParams(window.location.search).get('raw_q')).toBe('strawberries')
})

test('an API failure shows the public source availability error', async () => {
  mockSearchEverydaySafety.mockRejectedValue(new Error('Source unavailable'))
  renderFoodPage()

  expect(
    await screen.findByText(
      /Unable to load public records. Check backend\/source availability/i,
    ),
  ).toBeInTheDocument()
})

test('a changed route initialQuery reloads the normalized Food query', async () => {
  const { rerender } = renderFoodPage()

  await screen.findByRole('heading', { name: /Safety review for Chicken/i })
  window.history.replaceState(null, '', '?page=food-safety&q=Protein%20powder')
  rerender(
    <FoodSafetyPage
      initialQuery="  Protein   powder "
      goToPage={mockGoToPage}
    />,
  )

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenLastCalledWith(
      'Protein powder',
      8,
      'food_supplement',
      'score',
    )
  })
  expect(
    screen.getByRole('heading', { name: /Safety review for Protein powder/i }),
  ).toBeInTheDocument()
})

test('a Food record row expands and collapses its verification details', async () => {
  const user = userEvent.setup()
  renderFoodPage()

  const product = await screen.findByTitle(chickenProduct)
  const details = product.closest('details')
  expect(details).not.toHaveAttribute('open')

  await user.click(product)
  expect(details).toHaveAttribute('open')
  expect(screen.getByText('Use by 06/20/2026; lot C26')).toBeInTheDocument()

  await user.click(product)
  expect(details).not.toHaveAttribute('open')
})
