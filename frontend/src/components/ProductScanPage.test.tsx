import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ProductScanPage from './ProductScanPage'

const mockGoToPage = vi.fn()
const createObjectURLMock = vi.fn(() => 'blob:product-label-preview')
const revokeObjectURLMock = vi.fn()

beforeEach(() => {
  mockGoToPage.mockReset()
  createObjectURLMock.mockClear()
  revokeObjectURLMock.mockClear()

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

test('shows a local image upload preview', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  const file = new File(['label image'], 'label.png', { type: 'image/png' })
  await user.upload(screen.getByLabelText(/Upload product label image/i), file)

  expect(createObjectURLMock).toHaveBeenCalledWith(file)
  expect(screen.getByRole('img', { name: /Uploaded label preview for label.png/i })).toHaveAttribute(
    'src',
    'blob:product-label-preview',
  )
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

  await user.click(screen.getByLabelText('Food Safety'))
  await user.click(submitButton)

  expect(mockGoToPage).toHaveBeenCalledWith('food-safety', 'Mango Coconut Water')
})

test('allows a typed confirmed query when no candidate is selected', async () => {
  const user = userEvent.setup()
  renderProductScanPage()

  await user.type(screen.getByLabelText(/Confirmed search term/i), 'Sunscreen SPF 50')
  await user.click(screen.getByLabelText('Cosmetic Safety'))
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
  expect(within(limitations).getByText(/No image is stored/i)).toBeInTheDocument()
})

