import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegionalHealthPulse from './RegionalHealthPulse'
import { searchRegionalHealth } from '../api/regionalHealth'

vi.mock('../api/regionalHealth', () => ({
  searchRegionalHealth: vi.fn(),
}))

const mockedSearchRegionalHealth = vi.mocked(searchRegionalHealth)

describe('RegionalHealthPulse', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('renders safe Regional Health Pulse scaffold copy', () => {
    render(<RegionalHealthPulse />)

    expect(screen.getByRole('heading', { name: /Review public-health signal scaffolds/i })).toBeInTheDocument()
    expect(screen.getByText(/not live CDC\/HHS surveillance yet/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Check Health Pulse/i })).toBeInTheDocument()
  })

  test('validates empty Health Pulse fields before searching', async () => {
    const user = userEvent.setup()

    render(<RegionalHealthPulse />)

    await user.selectOptions(screen.getByLabelText('Region'), '')
    await user.click(screen.getByRole('button', { name: /Check Health Pulse/i }))

    expect(
      screen.getByText(/Enter both a region and a public-health category/i),
    ).toBeInTheDocument()
    expect(mockedSearchRegionalHealth).not.toHaveBeenCalled()
  })

  test('searches and renders a public-health signal summary', async () => {
    const user = userEvent.setup()

    mockedSearchRegionalHealth.mockResolvedValue({
      module: 'RegionalHealthPulse',
      region: 'MN',
      category: 'respiratory',
      source_id: 'regional_health_pulse_demo',
      source_name: 'Regional Health Pulse MVP scaffold',
      endpoint: 'https://healthdata.gov/',
      query: 'region=MN category=respiratory',
      retrieval_timestamp: '2026-05-26T18:00:00Z',
      record_count: 2,
      source_freshness: {
        freshness_status: 'scaffold',
        freshness_label: 'Scaffold data',
        source_update_cadence: 'MVP scaffold data; live CDC/HHS update cadence is not configured yet.',
        freshness_message:
          'Regional Health Pulse is using MVP scaffold data. Live CDC/HHS freshness checks are not configured yet.',
      },
      latest_period: '2026-W19',
      latest_value: 46,
      previous_period: '2026-W18',
      previous_value: 32,
      signal: {
        trend_label: 'Increasing',
        review_priority: 'Watch',
        confidence: 'Moderate',
        change_percent: 43.75,
        signal_version: 'regional-health-signal-v0.1',
        limitations: [
          'Regional Health Pulse uses public-data signals only. It is not medical advice, diagnosis, treatment guidance, emergency guidance, clinical decision support, or a personal disease-risk prediction.',
        ],
      },
      records: [],
      disclaimer:
        'Regional Health Pulse uses public-data signals only. It is not medical advice, diagnosis, treatment guidance, emergency guidance, clinical decision support, or a personal disease-risk prediction.',
      audit: {
        audit_id: '33333333-3333-4333-8333-333333333333',
        source_id: 'regional_health_pulse_demo',
        module: 'RegionalHealthPulse',
        upstream_status: 'success',
        record_count: 2,
        transform_version: 'regional-health-transform-v0.1',
        source_snapshot_status: 'skipped',
        source_pull_id: null,
        source_payload_hash: null,
      },
    })

    render(<RegionalHealthPulse />)

    await user.click(screen.getByRole('button', { name: /Check Health Pulse/i }))

    await waitFor(() => {
      expect(mockedSearchRegionalHealth).toHaveBeenCalledWith('MN', 'respiratory')
      expect(screen.getByRole('heading', { name: /Increasing public-health signal/i })).toBeInTheDocument()
      expect(screen.getAllByText(/Watch/i).length).toBeGreaterThan(0)
      expect(screen.getByText(/regional_health_pulse_demo/i)).toBeInTheDocument()
      expect(screen.getByText('Data trust status')).toBeInTheDocument()
      expect(screen.getByText('Scaffold data')).toBeInTheDocument()
      expect(screen.getByText(/Live CDC\/HHS freshness checks are not configured yet/i)).toBeInTheDocument()
      expect(screen.getByText('Technical provenance')).toBeInTheDocument()
      expect(screen.getByText('33333333-3333-4333-8333-333333333333')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Open in Audit History' })).toHaveAttribute(
        'href',
        '/?page=audit&audit_id=33333333-3333-4333-8333-333333333333',
      )
      expect(screen.getByText('regional-health-transform-v0.1')).toBeInTheDocument()
      expect(screen.getAllByText(/not medical advice/i).length).toBeGreaterThan(0)
    })
  })
})
