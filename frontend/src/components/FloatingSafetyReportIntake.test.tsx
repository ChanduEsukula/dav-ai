import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FloatingSafetyReportIntake from './FloatingSafetyReportIntake'
import { downloadSafetyIntelligenceReport } from '../api/reports'

vi.mock('../api/reports', async () => {
  const actual = await vi.importActual<typeof import('../api/reports')>(
    '../api/reports'
  )

  return {
    ...actual,
    downloadSafetyIntelligenceReport: vi.fn(),
  }
})

const mockDownloadSafetyIntelligenceReport = vi.mocked(
  downloadSafetyIntelligenceReport
)

beforeEach(() => {
  mockDownloadSafetyIntelligenceReport.mockReset()
})

test('opens the floating safety report intake drawer', async () => {
  const user = userEvent.setup()

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  expect(
    screen.getByRole('heading', { name: /Generate a Safety Report/i })
  ).toBeInTheDocument()

  expect(screen.getByLabelText(/What do you want to check/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/Search topic/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/Who is this for/i)).toBeInTheDocument()
})

test('does not expose unsupported report types in the intake dropdown', async () => {
  const user = userEvent.setup()

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  expect(screen.getByRole('option', { name: /Drug \/ product recall/i })).toBeInTheDocument()
  expect(screen.getByRole('option', { name: /Drug safety signal/i })).toBeInTheDocument()
  expect(screen.getByRole('option', { name: /Food \/ product recall/i })).toBeInTheDocument()
  expect(screen.getByRole('option', { name: /Cosmetic product signal/i })).toBeInTheDocument()

  expect(
    screen.queryByRole('option', { name: /Medical device/i })
  ).not.toBeInTheDocument()

  expect(
    screen.queryByRole('option', { name: /General safety briefing/i })
  ).not.toBeInTheDocument()
})

test('uses backend-safe public_health_analyst role when downloading a report', async () => {
  const user = userEvent.setup()

  mockDownloadSafetyIntelligenceReport.mockResolvedValue(
    'dav-ai-safety-report.pdf'
  )

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  await user.type(screen.getByLabelText(/Search topic/i), 'metformin')

  await user.selectOptions(
    screen.getByLabelText(/Who is this for/i),
    'public_health_analyst'
  )

  await user.click(
    screen.getByLabelText(/I understand this uses public FDA\/openFDA-style data only/i)
  )

  await user.click(
    screen.getByLabelText(/I understand this is not medical advice/i)
  )

  await user.click(
    screen.getByRole('button', { name: /Review report request/i })
  )

  expect(
    screen.getByRole('heading', { name: /Review before generation/i })
  ).toBeInTheDocument()

  expect(screen.getByText(/Public-health analyst/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Generate preview/i }))

  expect(
    screen.getByRole('heading', { name: /metformin safety report/i })
  ).toBeInTheDocument()

  await user.click(
    screen.getByRole('button', { name: /Download PDF report/i })
  )

  await waitFor(() => {
    expect(mockDownloadSafetyIntelligenceReport).toHaveBeenCalledTimes(1)
  })

  expect(mockDownloadSafetyIntelligenceReport).toHaveBeenCalledWith(
    expect.objectContaining({
      prepared_for: 'Public-health analyst',
      organization: 'DAV AI',
      role: 'public_health_analyst',
      query: 'metformin',
      module: 'recallradar',
    })
  )

  expect(
    screen.getByText(/Downloaded dav-ai-safety-report\.pdf/i)
  ).toBeInTheDocument()
})

test('uses FoodRadar module when food product recall is selected', async () => {
  const user = userEvent.setup()

  mockDownloadSafetyIntelligenceReport.mockResolvedValue(
    'dav-ai-food-report.pdf'
  )

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  await user.selectOptions(
    screen.getByLabelText(/What do you want to check/i),
    'food_product_recall'
  )

  await user.type(screen.getByLabelText(/Search topic/i), 'protein powder')

  await user.click(
    screen.getByLabelText(/I understand this uses public FDA\/openFDA-style data only/i)
  )

  await user.click(
    screen.getByLabelText(/I understand this is not medical advice/i)
  )

  await user.click(
    screen.getByRole('button', { name: /Review report request/i })
  )

  expect(screen.getByText(/FoodRadar/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Generate preview/i }))

  await user.click(
    screen.getByRole('button', { name: /Download PDF report/i })
  )

  await waitFor(() => {
    expect(mockDownloadSafetyIntelligenceReport).toHaveBeenCalledWith(
      expect.objectContaining({
        query: 'protein powder',
        module: 'foodradar',
      })
    )
  })
})

test('uses CosmeticSignal module when cosmetic product signal is selected', async () => {
  const user = userEvent.setup()

  mockDownloadSafetyIntelligenceReport.mockResolvedValue(
    'dav-ai-cosmetic-signal-report.pdf'
  )

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  await user.selectOptions(
    screen.getByLabelText(/What do you want to check/i),
    'cosmetic_product_signal'
  )

  await user.type(screen.getByLabelText(/Search topic/i), 'sunscreen')

  await user.click(
    screen.getByLabelText(/I understand this uses public FDA\/openFDA-style data only/i)
  )

  await user.click(
    screen.getByLabelText(/I understand this is not medical advice/i)
  )

  await user.click(
    screen.getByRole('button', { name: /Review report request/i })
  )

  expect(screen.getByText(/CosmeticSignal/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Generate preview/i }))

  await user.click(
    screen.getByRole('button', { name: /Download PDF report/i })
  )

  await waitFor(() => {
    expect(mockDownloadSafetyIntelligenceReport).toHaveBeenCalledWith(
      expect.objectContaining({
        query: 'sunscreen',
        module: 'cosmeticsignal',
      })
    )
  })
})

test('uses DrugSignal module when drug safety signal is selected', async () => {
  const user = userEvent.setup()

  mockDownloadSafetyIntelligenceReport.mockResolvedValue(
    'dav-ai-drug-signal-report.pdf'
  )

  render(<FloatingSafetyReportIntake />)

  await user.click(
    screen.getByRole('button', { name: /Open safety report intake/i })
  )

  await user.selectOptions(
    screen.getByLabelText(/What do you want to check/i),
    'drug_safety_signal'
  )

  await user.type(screen.getByLabelText(/Search topic/i), 'aspirin')

  await user.click(
    screen.getByLabelText(/I understand this uses public FDA\/openFDA-style data only/i)
  )

  await user.click(
    screen.getByLabelText(/I understand this is not medical advice/i)
  )

  await user.click(
    screen.getByRole('button', { name: /Review report request/i })
  )

  expect(screen.getByText(/DrugSignal/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Generate preview/i }))

  await user.click(
    screen.getByRole('button', { name: /Download PDF report/i })
  )

  await waitFor(() => {
    expect(mockDownloadSafetyIntelligenceReport).toHaveBeenCalledWith(
      expect.objectContaining({
        query: 'aspirin',
        module: 'drugsignal',
      })
    )
  })
})