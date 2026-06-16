import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { searchDocs, type StaticDocsSearchResponse } from '../api/docs'
import HelpDocsSearch from './HelpDocsSearch'

vi.mock('../api/docs', () => ({
  searchDocs: vi.fn(),
}))

const mockSearchDocs = vi.mocked(searchDocs)

function createDocsResponse(
  overrides: Partial<StaticDocsSearchResponse> = {},
): StaticDocsSearchResponse {
  return {
    query: 'ProductScan OCR',
    count: 1,
    results: [
      {
        title: 'ProductScan OCR V2 Plan',
        source_path: 'docs/productscan/PRODUCTSCAN_OCR_V2_PLAN.md',
        section_heading: 'Browser OCR intake',
        snippet:
          'ProductScan uses browser-side OCR as user-reviewed input assistance only.',
        matched_terms: ['ProductScan', 'OCR'],
        line_start: 12,
        line_end: 14,
      },
    ],
    limitations: [
      'Documentation search only. Results are snippets from Dav AI repository documentation.',
      'Not medical advice.',
      'Not a safety determination for any product, drug, food, supplement, or cosmetic.',
      'Verify official FDA/USDA sources before acting.',
    ],
    ...overrides,
  }
}

function createDeferredResponse() {
  let resolve: (value: StaticDocsSearchResponse) => void = () => {}
  const promise = new Promise<StaticDocsSearchResponse>((promiseResolve) => {
    resolve = promiseResolve
  })

  return { promise, resolve }
}

describe('HelpDocsSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls docs search from the search input', async () => {
    const user = userEvent.setup()
    mockSearchDocs.mockResolvedValue(createDocsResponse())

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), 'ProductScan OCR')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    await waitFor(() => {
      expect(mockSearchDocs).toHaveBeenCalledWith('ProductScan OCR', 8)
    })
  })

  it('requires at least two non-whitespace characters before searching', async () => {
    const user = userEvent.setup()

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), ' x ')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    expect(mockSearchDocs).not.toHaveBeenCalled()
    expect(
      screen.getByText(/Enter at least two non-whitespace characters/i),
    ).toBeInTheDocument()
  })

  it('renders a loading state while docs search is pending', async () => {
    const user = userEvent.setup()
    const deferred = createDeferredResponse()
    mockSearchDocs.mockReturnValue(deferred.promise)

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), 'ProductScan')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    expect(screen.getByRole('status')).toHaveTextContent(/Searching documentation/i)
    expect(screen.getByRole('button', { name: /Searching/i })).toBeDisabled()

    deferred.resolve(createDocsResponse())
    await screen.findByText('ProductScan OCR V2 Plan')
  })

  it('renders result snippets, source paths, headings, line ranges, and matched terms', async () => {
    const user = userEvent.setup()
    mockSearchDocs.mockResolvedValue(createDocsResponse())

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), 'ProductScan OCR')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    const title = await screen.findByText('ProductScan OCR V2 Plan')
    const result = title.closest('article')

    expect(result).not.toBeNull()
    if (!result) {
      throw new Error('Expected docs result article to render')
    }

    expect(within(result).getByText('ProductScan OCR V2 Plan')).toBeInTheDocument()
    expect(
      within(result).getByText('docs/productscan/PRODUCTSCAN_OCR_V2_PLAN.md'),
    ).toBeInTheDocument()
    expect(within(result).getByText('Section: Browser OCR intake')).toBeInTheDocument()
    expect(within(result).getByText('Lines 12-14')).toBeInTheDocument()
    expect(
      within(result).getByText(
        'ProductScan uses browser-side OCR as user-reviewed input assistance only.',
      ),
    ).toBeInTheDocument()
    expect(within(result).getByText('ProductScan')).toBeInTheDocument()
    expect(within(result).getByText('OCR')).toBeInTheDocument()
  })

  it('renders an empty state when no docs match', async () => {
    const user = userEvent.setup()
    mockSearchDocs.mockResolvedValue(
      createDocsResponse({
        query: 'zzzzmissing',
        count: 0,
        results: [],
      }),
    )

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), 'zzzzmissing')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    expect(
      await screen.findByText('No matching documentation snippets found.'),
    ).toBeInTheDocument()
  })

  it('renders an error state when docs search fails', async () => {
    const user = userEvent.setup()
    mockSearchDocs.mockRejectedValue(new Error('backend unavailable'))

    render(<HelpDocsSearch />)

    await user.type(screen.getByLabelText(/Search Dav AI docs/i), 'ProductScan')
    await user.click(screen.getByRole('button', { name: /Search docs/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /Unable to search documentation/i,
    )
  })

  it('keeps documentation search limitations visible', () => {
    render(<HelpDocsSearch />)

    const boundaries = screen.getByRole('complementary', {
      name: /Search boundaries/i,
    })

    expect(within(boundaries).getByText(/Documentation search only/i)).toBeInTheDocument()
    expect(within(boundaries).getByText('Not medical advice.')).toBeInTheDocument()
    expect(within(boundaries).getByText(/Not a safety determination/i)).toBeInTheDocument()
    expect(
      within(boundaries).getByText('Verify official FDA/USDA sources before acting.'),
    ).toBeInTheDocument()
  })
})
