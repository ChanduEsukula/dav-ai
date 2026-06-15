import { AxiosError } from 'axios'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SavedMonitorsPage from './SavedMonitorsPage'
import {
  createSavedMonitor,
  deleteSavedMonitor,
  getSavedMonitorInsight,
  listSavedMonitorRuns,
  listSavedMonitors,
  runSavedMonitor,
} from '../api/savedMonitors'
import type {
  MonitorInsight,
  SavedMonitor,
  SavedMonitorRun,
} from '../api/savedMonitors'

vi.mock('../api/savedMonitors', () => ({
  listSavedMonitors: vi.fn(),
  listSavedMonitorRuns: vi.fn(),
  getSavedMonitorInsight: vi.fn(),
  createSavedMonitor: vi.fn(),
  deleteSavedMonitor: vi.fn(),
  runSavedMonitor: vi.fn(),
}))

const baseMonitor: SavedMonitor = {
  id: 'monitor-1',
  name: 'Eye drops monitor',
  query: 'eye drops',
  module: 'recallradar',
  created_at: '2026-05-11T12:00:00Z',
  last_checked_at: null,
  latest_audit_id: null,
  latest_score: null,
  previous_score: null,
  latest_record_count: null,
  previous_record_count: null,
  status: 'not_checked',
}

const checkedMonitor: SavedMonitor = {
  ...baseMonitor,
  latest_audit_id: '11111111-1111-1111-1111-111111111111',
  latest_score: 74,
  previous_score: 68,
  latest_record_count: 5,
  previous_record_count: 3,
  status: 'checked',
  last_checked_at: '2026-05-11T13:00:00Z',
}

const healthPulseMonitor: SavedMonitor = {
  ...baseMonitor,
  id: 'monitor-health-pulse',
  name: 'Minnesota respiratory monitor',
  query: 'MN respiratory',
  module: 'regional_health_pulse',
  latest_audit_id: '33333333-3333-3333-3333-333333333333',
  latest_score: 46,
  previous_score: 32,
  latest_record_count: 2,
  previous_record_count: 2,
  status: 'checked',
  last_checked_at: '2026-05-26T18:00:00Z',
}

const baseRun: SavedMonitorRun = {
  run_id: 'run-1',
  monitor_id: 'monitor-1',
  module: 'recallradar',
  query: 'eye drops',
  status: 'success',
  record_count: 5,
  score: 74,
  score_label: 'Medium',
  audit_id: '11111111-1111-1111-1111-111111111111',
  created_at: '2026-05-11T13:05:00Z',
  error_message: null,
  payload_change: {
    label: 'changed',
    previous_hash: 'a'.repeat(64),
    latest_hash: 'b'.repeat(64),
    reason: 'Latest payload hash differs from the previous payload hash.',
    safety_note:
      'Payload-change status is an operational public-data review signal based on stored payload hashes. It does not prove medical risk, clinical urgency, product danger, causation, or source correctness.',
  },
}

const baseInsight: MonitorInsight = {
  monitor_id: 'monitor-1',
  label: 'stable',
  headline: 'Stable public-data activity',
  explanation:
    'The latest successful saved monitor run is similar to the previous successful run in stored Dav AI public-data history.',
  latest_run_id: 'run-2',
  previous_run_id: 'run-1',
  latest_record_count: 5,
  previous_record_count: 3,
  record_count_delta: 2,
  percent_change: 66.67,
  latest_score: 74,
  previous_score: 68,
  score_delta: 6,
  confidence: 'medium',
  insight_version: 'monitor-insight-v0.1',
  limitation:
    'This insight is based only on stored Dav AI public-data monitor history. It is not medical advice, diagnosis, treatment guidance, clinical decision support, or proof of causality.',
}

function expectTextContent(pattern: RegExp) {
  expect(
    screen.getByText((_, element) => {
      const text = element?.textContent ?? ''
      const children = Array.from(element?.children ?? [])

      return (
        pattern.test(text) &&
        children.every((child) => !pattern.test(child.textContent ?? ''))
      )
    }),
  ).toBeInTheDocument()
}

describe('SavedMonitorsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
    vi.mocked(listSavedMonitorRuns).mockResolvedValue([])
    vi.mocked(getSavedMonitorInsight).mockResolvedValue(baseInsight)
    window.history.replaceState(null, '', '/')
  })

  it('renders loading state and empty state', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    expect(screen.getByText('Loading saved monitors...')).toBeInTheDocument()

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })
  })

  it('renders saved monitors returned by the API with latest, previous, change values, and AI insight', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([checkedMonitor])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expectTextContent(/Query:\s*eye drops/i)
      expect(screen.getAllByText('RecallRadar').length).toBeGreaterThan(0)
      expectTextContent(/RecallRadar\s*·\s*checked/i)
      expect(screen.getByText('Latest score')).toBeInTheDocument()
      expect(screen.getByText('74')).toBeInTheDocument()
      expectTextContent(/Previous:\s*68/i)
      expect(screen.getByText('Records')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expectTextContent(/Previous:\s*3/i)
      expect(screen.getByText('Score +6')).toBeInTheDocument()
      expect(screen.getByText('Records +2')).toBeInTheDocument()
      expect(screen.getByText('Monitor Insight')).toBeInTheDocument()
      expect(screen.getByText('Stable')).toBeInTheDocument()
      expect(screen.getByText('Stable public-data activity')).toBeInTheDocument()
      expect(screen.getByText('monitor-insight-v0.1')).toBeInTheDocument()
      expect(screen.getByText(/not medical advice/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
      expect(screen.getByText('No manual run history yet.')).toBeInTheDocument()
    })
  })

  it('renders Regional Health Pulse saved monitors', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([healthPulseMonitor])
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      monitor_id: 'monitor-health-pulse',
      headline: 'Regional public-data activity increased',
      latest_record_count: 2,
      previous_record_count: 2,
      latest_score: 46,
      previous_score: 32,
      score_delta: 14,
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Minnesota respiratory monitor')).toBeInTheDocument()
      expectTextContent(/Query:\s*MN respiratory/i)
      expect(screen.getAllByText('Regional Health Pulse').length).toBeGreaterThan(0)
      expectTextContent(/Regional Health Pulse\s*·\s*checked/i)
      expect(screen.getByText('46')).toBeInTheDocument()
      expectTextContent(/Previous:\s*32/i)
      expect(screen.getByText('Score +14')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
    })
  })

  it('renders saved monitor run history returned by the API', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        status: 'checked',
        latest_score: 74,
        latest_record_count: 5,
      },
    ])
    vi.mocked(listSavedMonitorRuns).mockResolvedValue([baseRun])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByText(/RecallRadar · success/i)).toBeInTheDocument()
      expect(screen.getByText('Records 5')).toBeInTheDocument()
      expect(screen.getByText('74 Medium')).toBeInTheDocument()
      expect(screen.getByText('Payload: Changed')).toBeInTheDocument()
      expect(
        screen.getByText('Latest payload hash differs from the previous payload hash.'),
      ).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View run audit' })).toBeInTheDocument()
    })
  })

  it('renders run history empty state for a monitor with no runs', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([baseMonitor])
    vi.mocked(listSavedMonitorRuns).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByText('No manual run history yet.')).toBeInTheDocument()
    })
  })

  it('opens Audit History URL state from a run-history audit link', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([baseMonitor])
    vi.mocked(listSavedMonitorRuns).mockResolvedValue([baseRun])
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')
    const pushStateSpy = vi.spyOn(window.history, 'pushState')

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'View run audit' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'View run audit' }))

    expect(window.location.search).toContain('page=audit')
    expect(window.location.search).toContain(
      'audit_id=11111111-1111-1111-1111-111111111111',
    )
    expect(pushStateSpy).toHaveBeenCalled()
    expect(dispatchSpy).toHaveBeenCalled()

    pushStateSpy.mockRestore()
    dispatchSpy.mockRestore()
  })

  it('renders unchanged and negative change indicators', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        id: 'monitor-2',
        name: 'Metformin monitor',
        query: 'metformin',
        module: 'drugsignal',
        latest_score: 80,
        previous_score: 80,
        latest_record_count: 6,
        previous_record_count: 9,
        status: 'checked',
      },
    ])
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      monitor_id: 'monitor-2',
      label: 'decreased',
      headline: 'Public-data activity decreased',
      record_count_delta: -3,
      percent_change: -33.33,
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Metformin monitor')).toBeInTheDocument()
      expect(screen.getAllByText('DrugSignal').length).toBeGreaterThan(0)
      expect(screen.getByText('Score unchanged')).toBeInTheDocument()
      expect(screen.getByText('Records -3')).toBeInTheDocument()
      expect(screen.getByText('Public-data activity decreased')).toBeInTheDocument()
    })
  })

  it('renders N/A change indicators when previous values do not exist', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        latest_score: 70,
        previous_score: null,
        latest_record_count: 8,
        previous_record_count: null,
      },
    ])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByText('Score N/A')).toBeInTheDocument()
      expect(screen.getByText('Records N/A')).toBeInTheDocument()
    })
  })

  it('creates a saved monitor and adds it to the list', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])
    vi.mocked(createSavedMonitor).mockResolvedValue({
      ...baseMonitor,
      id: 'monitor-created',
      name: 'Metformin monitor',
      query: 'metformin',
      module: 'drugsignal',
    })
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      monitor_id: 'monitor-created',
      label: 'insufficient_history',
      headline: 'Insufficient history',
      latest_record_count: null,
      previous_record_count: null,
      record_count_delta: null,
      percent_change: null,
      confidence: 'low',
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Monitor name'), {
      target: { value: 'Metformin monitor' },
    })
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'metformin' },
    })
    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'drugsignal' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save Monitor' }))

    await waitFor(() => {
      expect(createSavedMonitor).toHaveBeenCalledWith({
        name: 'Metformin monitor',
        query: 'metformin',
        module: 'drugsignal',
      })
      expect(screen.getByText('Metformin monitor')).toBeInTheDocument()
      expectTextContent(/Query:\s*metformin/i)
      expect(screen.getAllByText('DrugSignal').length).toBeGreaterThan(0)
      expect(screen.getByText('Score N/A')).toBeInTheDocument()
      expect(screen.getByText('Records N/A')).toBeInTheDocument()
      expect(screen.getByText('Insufficient history')).toBeInTheDocument()
    })
  })

  it('hides CosmeticSignal from monitor creation until backend parity exists', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    expect(screen.queryByRole('option', { name: 'CosmeticSignal' })).not.toBeInTheDocument()
    expect(screen.getByText(/Cosmetic monitor creation/i)).toBeInTheDocument()
  })

  it('creates a Regional Health Pulse saved monitor with query guidance', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])
    vi.mocked(createSavedMonitor).mockResolvedValue({
      ...healthPulseMonitor,
      id: 'monitor-created-health-pulse',
    })
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      monitor_id: 'monitor-created-health-pulse',
      label: 'insufficient_history',
      headline: 'Insufficient history',
      latest_record_count: null,
      previous_record_count: null,
      record_count_delta: null,
      percent_change: null,
      latest_score: null,
      previous_score: null,
      score_delta: null,
      confidence: 'low',
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'regional_health_pulse' },
    })

    expect(
      screen.getByText(/Use format: MN respiratory/i),
    ).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Monitor name'), {
      target: { value: 'Minnesota respiratory monitor' },
    })
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'MN respiratory' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save Monitor' }))

    await waitFor(() => {
      expect(createSavedMonitor).toHaveBeenCalledWith({
        name: 'Minnesota respiratory monitor',
        query: 'MN respiratory',
        module: 'regional_health_pulse',
      })
      expect(screen.getByText('Minnesota respiratory monitor')).toBeInTheDocument()
      expect(screen.getAllByText('Regional Health Pulse').length).toBeGreaterThan(0)
      expect(screen.getByText('Insufficient history')).toBeInTheDocument()
    })
  })

  it('trims leading and trailing spaces but preserves internal query spaces', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])
    vi.mocked(createSavedMonitor).mockResolvedValue({
      ...healthPulseMonitor,
      id: 'monitor-spaces',
      name: 'Minnesota respiratory monitor',
      query: 'MN hospital pressure',
      module: 'regional_health_pulse',
    })
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      monitor_id: 'monitor-spaces',
      label: 'insufficient_history',
      headline: 'Insufficient history',
      latest_record_count: null,
      previous_record_count: null,
      record_count_delta: null,
      percent_change: null,
      latest_score: null,
      previous_score: null,
      score_delta: null,
      confidence: 'low',
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'regional_health_pulse' },
    })
    fireEvent.change(screen.getByLabelText('Monitor name'), {
      target: { value: '  Minnesota respiratory monitor  ' },
    })
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: '  MN hospital pressure  ' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save Monitor' }))

    await waitFor(() => {
      expect(createSavedMonitor).toHaveBeenCalledWith({
        name: 'Minnesota respiratory monitor',
        query: 'MN hospital pressure',
        module: 'regional_health_pulse',
      })
    })
  })

  it('shows duplicate saved monitor error from the API', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])
    vi.mocked(createSavedMonitor).mockRejectedValue(
      new AxiosError(
        'duplicate monitor',
        'ERR_BAD_REQUEST',
        undefined,
        undefined,
        {
          data: {
            detail: 'A saved monitor already exists for this module and query.',
          },
          status: 409,
          statusText: 'Conflict',
          headers: {},
          config: {
            headers: {} as never,
          },
        },
      ),
    )

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Monitor name'), {
      target: { value: 'Eye drops duplicate' },
    })
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'eye drops' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save Monitor' }))

    await waitFor(() => {
      expect(
        screen.getByText('A saved monitor already exists for this module and query.'),
      ).toBeInTheDocument()
    })
  })

  it('shows validation error for short name or query', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText(
          'No saved monitors yet. Create one above to start the monitoring workflow.',
        ),
      ).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Monitor name'), {
      target: { value: 'x' },
    })
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'y' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save Monitor' }))

    expect(
      screen.getByText('Name and query must each be at least 2 characters.'),
    ).toBeInTheDocument()
    expect(createSavedMonitor).not.toHaveBeenCalled()
  })

  it('runs a saved monitor check and updates latest, previous, change values, and insight', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        latest_score: 70,
        previous_score: null,
        latest_record_count: 8,
        previous_record_count: null,
      },
    ])
    vi.mocked(runSavedMonitor).mockResolvedValue({
      ...baseMonitor,
      status: 'checked',
      latest_score: 88,
      previous_score: 70,
      latest_record_count: 12,
      previous_record_count: 8,
      latest_audit_id: '22222222-2222-2222-2222-222222222222',
      last_checked_at: '2026-05-11T14:00:00Z',
    })
    vi.mocked(getSavedMonitorInsight).mockResolvedValue({
      ...baseInsight,
      latest_record_count: 12,
      previous_record_count: 8,
      record_count_delta: 4,
      percent_change: 50,
      latest_score: 88,
      previous_score: 70,
      score_delta: 18,
    })

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Run Check' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Run Check' }))

    await waitFor(() => {
      expect(runSavedMonitor).toHaveBeenCalledWith('monitor-1')
      expect(listSavedMonitorRuns).toHaveBeenCalledWith('monitor-1')
      expect(getSavedMonitorInsight).toHaveBeenCalledWith('monitor-1')
      expectTextContent(/RecallRadar\s*·\s*checked/i)
      expect(screen.getByText('88')).toBeInTheDocument()
      expectTextContent(/Previous:\s*70/i)
      expect(screen.getByText('12')).toBeInTheDocument()
      expectTextContent(/Previous:\s*8/i)
      expect(screen.getByText('Score +18')).toBeInTheDocument()
      expect(screen.getByText('Records +4')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
      expect(screen.getByText('Stable public-data activity')).toBeInTheDocument()
    })
  })

  it('deletes a saved monitor from the list when confirmed', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([baseMonitor])
    vi.mocked(deleteSavedMonitor).mockResolvedValue()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith(
        'Are you sure you want to delete this saved monitor?',
      )
      expect(deleteSavedMonitor).toHaveBeenCalledWith('monitor-1')
      expect(screen.queryByText('Eye drops monitor')).not.toBeInTheDocument()
    })
  })

  it('does not delete a saved monitor when delete confirmation is cancelled', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([baseMonitor])
    vi.mocked(deleteSavedMonitor).mockResolvedValue()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith(
      'Are you sure you want to delete this saved monitor?',
    )
    expect(deleteSavedMonitor).not.toHaveBeenCalled()
    expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
  })

  it('opens Audit History URL state from View Audit button', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        latest_audit_id: '33333333-3333-3333-3333-333333333333',
      },
    ])

    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')
    const pushStateSpy = vi.spyOn(window.history, 'pushState')

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'View Audit' }))

    expect(window.location.search).toContain('page=audit')
    expect(window.location.search).toContain(
      'audit_id=33333333-3333-3333-3333-333333333333',
    )
    expect(pushStateSpy).toHaveBeenCalled()
    expect(dispatchSpy).toHaveBeenCalled()

    pushStateSpy.mockRestore()
    dispatchSpy.mockRestore()
  })

  it('shows load error when saved monitors cannot be loaded', async () => {
    vi.mocked(listSavedMonitors).mockRejectedValue(new Error('network error'))

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load saved monitors.')).toBeInTheDocument()
    })
  })

  it('shows run error when a monitor check fails', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([baseMonitor])
    vi.mocked(runSavedMonitor).mockRejectedValue(new Error('run failed'))

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Run Check' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Run Check' }))

    await waitFor(() => {
      expect(screen.getByText('Unable to run saved monitor check.')).toBeInTheDocument()
    })
  })
})
