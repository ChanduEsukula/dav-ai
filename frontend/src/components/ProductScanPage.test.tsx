import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { analyzeProductScanImageQuality } from '../utils/productScanImageQuality'
import { runProductScanOcr } from '../utils/productScanOcr'
import ProductScanPage from './ProductScanPage'

vi.mock('../utils/productScanImageQuality', () => ({
  analyzeProductScanImageQuality: vi.fn(),
}))

vi.mock('../utils/productScanOcr', () => ({
  runProductScanOcr: vi.fn(),
}))

const mockGoToPage = vi.fn()
const mockAnalyzeProductScanImageQuality = vi.mocked(analyzeProductScanImageQuality)
const mockRunProductScanOcr = vi.mocked(runProductScanOcr)
const createObjectURLMock = vi.fn(() => 'blob:product-label-preview')
const revokeObjectURLMock = vi.fn()

beforeEach(() => {
  mockGoToPage.mockReset()
  mockAnalyzeProductScanImageQuality.mockReset()
  mockRunProductScanOcr.mockReset()
  createObjectURLMock.mockClear()
  revokeObjectURLMock.mockClear()

  mockAnalyzeProductScanImageQuality.mockResolvedValue({
    width: 1200,
    height: 900,
    fileSizeBytes: 120_000,
    brightness: 136,
    contrast: 54,
    warnings: [],
  })

  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    value: createObjectURLMock,
  })
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    value: revokeObjectURLMock,
  })
})

function renderProductScanPage() {
  return render(<ProductScanPage goToPage={mockGoToPage} />)
}

async function uploadLabelImage(user: ReturnType<typeof userEvent.setup>) {
  const file = new File(['label image'], 'label.png', { type: 'image/png' })
  await user.upload(screen.getByLabelText(/Upload product label image/i), file)
  return file
}

test('shows a local image upload preview', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  const file = await uploadLabelImage(user)

  expect(createObjectURLMock).toHaveBeenCalledWith(file)
  expect(screen.getByRole('img', { name: /Uploaded label preview for label.png/i })).toHaveAttribute(
    'src',
    'blob:product-label-preview',
  )
})

test('shows OCR button and not-started state after image upload', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  expect(screen.getByRole('status')).toHaveTextContent(/OCR not started/i)
  expect(
    screen.queryByRole('button', { name: /Extract text from image/i }),
  ).not.toBeInTheDocument()

  const file = await uploadLabelImage(user)

  expect(
    screen.getByRole('button', { name: /Extract text from image/i }),
  ).toBeInTheDocument()
  expect(mockAnalyzeProductScanImageQuality).toHaveBeenCalledWith(file)
  expect(
    await screen.findByText(/OCR can misread labels. Review extracted text before continuing/i),
  ).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent(
    /OCR not started. Select Extract text from image/i,
  )
})

test('shows local image quality warnings without blocking OCR', async () => {
  const user = userEvent.setup()
  mockAnalyzeProductScanImageQuality.mockResolvedValue({
    width: 320,
    height: 240,
    fileSizeBytes: 120_000,
    brightness: 42,
    contrast: 18,
    warnings: [
      {
        code: 'too-small',
        message: 'Image may be too small; try a closer label photo.',
      },
      {
        code: 'too-dark',
        message: 'Image may be too dark for reliable OCR.',
      },
    ],
  })
  renderProductScanPage()

  await uploadLabelImage(user)

  expect(
    await screen.findByText('Image may be too small; try a closer label photo.'),
  ).toBeInTheDocument()
  expect(screen.getByText('Image may be too dark for reliable OCR.')).toBeInTheDocument()
  expect(
    screen.getByText(/OCR can misread labels. Review extracted text before continuing/i),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Extract text from image/i })).toBeEnabled()
})

test('disables OCR when the uploaded image cannot be loaded and keeps manual fallback', async () => {
  const user = userEvent.setup()
  mockAnalyzeProductScanImageQuality.mockRejectedValue(new Error('image load failed'))
  renderProductScanPage()

  await uploadLabelImage(user)

  expect(await screen.findByRole('alert')).toHaveTextContent(/Image could not be loaded for OCR/i)
  expect(screen.getByRole('button', { name: /Extract text from image/i })).toBeDisabled()

  await user.type(
    screen.getByLabelText(/Paste or review extracted label text/i),
    'Product Name: Sunscreen SPF 50',
  )

  expect(screen.getByText('Sunscreen SPF 50')).toBeInTheDocument()
})

test('shows OCR running state while extraction is pending', async () => {
  const user = userEvent.setup()
  let resolveOcr: (value: string) => void = () => {}
  mockRunProductScanOcr.mockReturnValue(
    new Promise((resolve) => {
      resolveOcr = resolve
    }),
  )
  renderProductScanPage()

  await uploadLabelImage(user)
  await user.click(screen.getByRole('button', { name: /Extract text from image/i }))

  expect(screen.getByRole('button', { name: /Extracting text/i })).toBeDisabled()
  expect(screen.getByRole('status')).toHaveTextContent(/OCR running/i)

  resolveOcr('Product Name: Guava Juice')
  await waitFor(() => {
    expect(screen.getByRole('status')).toHaveTextContent(/OCR completed/i)
  })
})

test('successful OCR populates the manual text field and candidates', async () => {
  const user = userEvent.setup()
  mockRunProductScanOcr.mockResolvedValue(
    'Product Name: Guava Juice\nUPC: 012345678905\nLot A1B2C3',
  )
  renderProductScanPage()

  await uploadLabelImage(user)
  await user.click(screen.getByRole('button', { name: /Extract text from image/i }))

  await waitFor(() => {
    expect(screen.getByLabelText(/Paste or review extracted label text/i)).toHaveValue(
      'Product Name: Guava Juice\nUPC: 012345678905\nLot A1B2C3',
    )
  })
  expect(screen.getByRole('status')).toHaveTextContent(/OCR completed/i)
  expect(screen.getByText('Guava Juice')).toBeInTheDocument()
  expect(screen.getByText('012345678905')).toBeInTheDocument()
})

test('OCR failure shows fallback message and manual text still works', async () => {
  const user = userEvent.setup()
  mockRunProductScanOcr.mockRejectedValue(new Error('ocr failed'))
  renderProductScanPage()

  await uploadLabelImage(user)
  await user.click(screen.getByRole('button', { name: /Extract text from image/i }))

  expect(await screen.findByText(/OCR failed. You can still paste or type label text manually/i)).toBeInTheDocument()

  await user.type(
    screen.getByLabelText(/Paste or review extracted label text/i),
    'Product Name: Sunscreen SPF 50',
  )

  expect(screen.getByText('Sunscreen SPF 50')).toBeInTheDocument()
})

test('extracts candidates from manual label text', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  await user.type(
    screen.getByLabelText(/Paste or review extracted label text/i),
    'Product Name: Mango Coconut Water\nUPC: 012345678905\nLot A1B2C3\nBest by 05/2026',
  )

  expect(screen.getByText('Mango Coconut Water')).toBeInTheDocument()
  expect(screen.getByText('012345678905')).toBeInTheDocument()
  expect(screen.getByText('A1B2C3')).toBeInTheDocument()
  expect(screen.getByText('05/2026')).toBeInTheDocument()
})

test('requires workflow selection and routes confirmed query to an existing safety page', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  await user.type(
    screen.getByLabelText(/Paste or review extracted label text/i),
    'Product Name: Mango Coconut Water\nDistributed by Dav Foods',
  )
  await user.click(
    screen.getByRole('button', { name: /Use Mango Coconut Water as search term/i }),
  )

  const submitButton = screen.getByRole('button', { name: /Open selected workflow/i })
  expect(submitButton).toBeDisabled()

  await user.click(screen.getByLabelText('FoodSignal'))
  await user.click(submitButton)

  expect(mockGoToPage).toHaveBeenCalledWith('food-safety', 'Mango Coconut Water')
})

test('allows the user to edit OCR text before routing', async () => {
  const user = userEvent.setup()
  mockRunProductScanOcr.mockResolvedValue('Product Name: Guava Juice')
  renderProductScanPage()

  await uploadLabelImage(user)
  await user.click(screen.getByRole('button', { name: /Extract text from image/i }))

  const textField = await screen.findByLabelText(/Paste or review extracted label text/i)
  await waitFor(() => {
    expect(textField).toHaveValue('Product Name: Guava Juice')
  })

  await user.clear(textField)
  await user.type(textField, 'Product Name: Mango Juice')
  await user.click(screen.getByRole('button', { name: /Use Mango Juice as search term/i }))
  await user.click(screen.getByLabelText('FoodSignal'))
  await user.click(screen.getByRole('button', { name: /Open selected workflow/i }))

  expect(mockGoToPage).toHaveBeenCalledWith('food-safety', 'Mango Juice')
})

test('allows a typed confirmed query when no candidate is selected', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  await user.type(screen.getByLabelText(/Confirmed search term/i), 'Sunscreen SPF 50')
  await user.click(screen.getByLabelText('Personal Care Signals'))
  await user.click(screen.getByRole('button', { name: /Open selected workflow/i }))

  expect(mockGoToPage).toHaveBeenCalledWith('cosmetic-safety', 'Sunscreen SPF 50')
})

test('shows ProductScan limitations and no safety verdict language', () => {
  renderProductScanPage()

  const limitations = screen.getByRole('complementary', {
    name: /ProductScan limitations/i,
  })

  expect(
    within(limitations).getByText(/OCR or pasted text can be wrong/i),
  ).toBeInTheDocument()
  expect(
    within(limitations).getByText(/ProductScan does not determine whether a product is safe or unsafe/i),
  ).toBeInTheDocument()
  expect(
    within(limitations).getByText(/OCR can misread labels. Review and edit the extracted text before continuing/i),
  ).toBeInTheDocument()
  expect(within(limitations).getByText(/No image is stored/i)).toBeInTheDocument()
})
