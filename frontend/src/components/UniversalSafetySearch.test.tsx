import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { searchCosmeticEvents, type CosmeticEventSearchResponse } from '../api/cosmeticEvents'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchEverydaySafety,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import { searchRecalls, type RecallSearchResponse } from '../api/recalls'
import UniversalSafetySearch from './UniversalSafetySearch'

vi.mock('../api/recalls', async () => {
  const actual = await vi.importActual<typeof import('../api/recalls')>('../api/recalls')
  return { ...actual, searchRecalls: vi.fn() }
})

vi.mock('../api/drugEvents', async () => {
  const actual = await vi.importActual<typeof import('../api/drugEvents')>('../api/drugEvents')
  return { ...actual, searchDrugEvents: vi.fn() }
})

vi.mock('../api/everydaySafety', async () => {
  const actual = await vi.importActual<typeof import('../api/everydaySafety')>(
    '../api/everydaySafety',
  )
  return { ...actual, searchEverydaySafety: vi.fn() }
})

vi.mock('../api/cosmeticEvents', async () => {
  const actual = await vi.importActual<typeof import('../api/cosmeticEvents')>(
    '../api/cosmeticEvents',
  )
  return { ...actual, searchCosmeticEvents: vi.fn() }
})

const mockSearchRecalls = vi.mocked(searchRecalls)
const mockSearchDrugEvents = vi.mocked(searchDrugEvents)
const mockSearchEverydaySafety = vi.mocked(searchEverydaySafety)
const mockSearchCosmeticEvents = vi.mocked(searchCosmeticEvents)
const mockGoToPage = vi.fn()

const recallResponse = { count: 1 } as RecallSearchResponse
const drugResponse = { count: 2 } as DrugEventSearchResponse
const foodResponse = { count: 3 } as EverydaySafetySearchResponse
const cosmeticResponse = { count: 4 } as CosmeticEventSearchResponse

beforeEach(() => {
  mockGoToPage.mockReset()
  mockSearchRecalls.mockReset()
  mockSearchDrugEvents.mockReset()
  mockSearchEverydaySafety.mockReset()
  mockSearchCosmeticEvents.mockReset()
  mockSearchRecalls.mockResolvedValue(recallResponse)
  mockSearchDrugEvents.mockResolvedValue(drugResponse)
  mockSearchEverydaySafety.mockResolvedValue(foodResponse)
  mockSearchCosmeticEvents.mockResolvedValue(cosmeticResponse)
})

test('shows quiet guidance for an empty universal search', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  await user.click(screen.getByRole('button', { name: 'Analyze' }))

  expect(screen.getByRole('status')).toHaveTextContent(
    /Enter a product, vehicle, drug, brand, food, supplement, cosmetic, identifier, or ingredient/i,
  )
  expect(mockSearchRecalls).not.toHaveBeenCalled()
})

test('normalizes universal search whitespace before API and route navigation', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  await user.type(
    screen.getByLabelText(/Safety search/i),
    '   xanax   xr  ',
  )
  await user.click(screen.getByRole('button', { name: 'Analyze' }))

  await waitFor(() => {
    expect(mockSearchRecalls).toHaveBeenCalledWith('xanax xr', 3)
  })
  expect(mockSearchDrugEvents).toHaveBeenCalledWith('xanax xr', 5)

  await user.click(await screen.findByRole('button', { name: 'Open Pharmacy Safety' }))
  expect(mockGoToPage).toHaveBeenCalledWith('pharmacy-safety', 'xanax xr')
})

test.each([
  ['XANAX', 'pharmacy', 'looks like a drug or medication search'],
  ['Chicken', 'food', 'looks like a food or supplement search'],
  ['Sunscreen SPF 50', 'cosmetic', 'looks like a cosmetic or personal-care search'],
] as const)(
  'routes the obvious %s example to %s predictably',
  async (query, area, previewText) => {
    const user = userEvent.setup()
    render(<UniversalSafetySearch goToPage={mockGoToPage} />)

    await user.type(screen.getByLabelText(/Safety search/i), query)
    await user.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByText(new RegExp(previewText, 'i'))).toBeInTheDocument()

    if (area === 'pharmacy') {
      expect(mockSearchRecalls).toHaveBeenCalledWith(query, 3)
    } else if (area === 'food') {
      expect(mockSearchEverydaySafety).toHaveBeenCalledWith(query, 5)
      expect(
        screen.getByText(/No result does not prove that a product is safe/i),
      ).toBeInTheDocument()
    } else {
      expect(mockSearchCosmeticEvents).toHaveBeenCalledWith(query, 5)
      expect(screen.getByText(/public reporting signals/i)).toBeInTheDocument()
    }
  },
)

test.each([
  'tire',
  'scooter',
  'air fryer',
  'car seat',
  'battery',
  'NDC 66715 6547',
  'Advil',
  'tylonal',
  'blood sugar monitor',
] as const)('routes %s to Public Safety Search from universal search', async (query) => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  await user.type(screen.getByLabelText(/Safety search/i), query)
  await user.click(screen.getByRole('button', { name: 'Analyze' }))

  expect(
    await screen.findByText(new RegExp(`${query} belongs in Public Safety Search`, 'i')),
  ).toBeInTheDocument()
  expect(mockSearchRecalls).not.toHaveBeenCalled()
  expect(mockSearchDrugEvents).not.toHaveBeenCalled()
  expect(mockSearchEverydaySafety).not.toHaveBeenCalled()
  expect(mockSearchCosmeticEvents).not.toHaveBeenCalled()

  await user.click(screen.getByRole('button', { name: 'Open Public Safety Search' }))
  expect(mockGoToPage).toHaveBeenCalledWith('public-safety', query)
})

test('does not repeat a completed equivalent universal search', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  const input = screen.getByLabelText(/Safety search/i)
  await user.type(input, 'Xanax')
  await user.click(screen.getByRole('button', { name: 'Analyze' }))
  await screen.findByText(/3 possible public records found/i)

  await user.clear(input)
  await user.type(input, '  XANAX  ')
  await user.click(screen.getByRole('button', { name: 'Analyze' }))

  expect(mockSearchRecalls).toHaveBeenCalledTimes(1)
  expect(mockSearchDrugEvents).toHaveBeenCalledTimes(1)
  expect(input).toHaveValue('XANAX')
})

test('example chips clear previous universal search guidance', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  await user.click(screen.getByRole('button', { name: 'Analyze' }))
  expect(screen.getByRole('status')).toHaveTextContent(
    /Enter a product, vehicle, drug, brand, food, supplement, cosmetic, identifier, or ingredient/i,
  )

  await user.click(screen.getByRole('button', { name: 'Chicken' }))

  expect(
    await screen.findByText(/Chicken looks like a food or supplement search/i),
  ).toBeInTheDocument()
  expect(
    screen.queryByText(
      /Enter a product, vehicle, drug, brand, food, supplement, cosmetic, identifier, or ingredient to search public records/i,
    ),
  ).not.toBeInTheDocument()
})

test('normalizes an approved homepage alias and preserves the original route query', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  const input = screen.getByLabelText(/Safety search/i)
  await user.type(input, 'strawberries')
  await user.click(screen.getByRole('button', { name: 'Analyze' }))

  await waitFor(() => {
    expect(mockSearchEverydaySafety).toHaveBeenCalledWith('strawberry', 5)
  })
  expect(
    screen.getByText(
      /Showing results for 'strawberry' based on your search 'strawberries'/i,
    ),
  ).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Open Food & Supplement Safety' }))
  expect(mockGoToPage).toHaveBeenCalledWith(
    'food-safety',
    'strawberry',
    'strawberries',
  )
})

test('homepage typeahead exposes workflow labels and supports keyboard selection', async () => {
  const user = userEvent.setup()
  render(<UniversalSafetySearch goToPage={mockGoToPage} />)

  const input = screen.getByLabelText(/Safety search/i)
  await user.type(input, 'xan')

  expect(
    screen.getByRole('option', { name: /xanax.*Pharmacy Safety/i }),
  ).toBeInTheDocument()

  await user.keyboard('{ArrowDown}{Enter}')
  expect(input).toHaveValue('xanax')
})
