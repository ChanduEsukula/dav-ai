import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SavedMonitorsPage from './SavedMonitorsPage'
import {
  createSavedMonitor,
  deleteSavedMonitor,
  listSavedMonitors,
  runSavedMonitor,
} from '../api/savedMonitors'
import type { SavedMonitor } from '../api/savedMonitors'

vi.mock('../api/savedMonitors', () => ({
  listSavedMonitors: vi.fn(),
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

describe('SavedMonitorsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
    window.history.replaceState(null, '', '/')
  })

  it('renders loading state and empty state', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    expect(screen.getByText('Loading saved monitors...')).toBeInTheDocument()

    await waitFor(() => {
      expect(
        screen.getByText('No saved monitors yet. Create one above to start the monitoring workflow.'),
      ).toBeInTheDocument()
    })
  })

  it('renders saved monitors returned by the API with latest and previous values', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([
      {
        ...baseMonitor,
        latest_audit_id: '11111111-1111-1111-1111-111111111111',
        latest_score: 74,
        previous_score: 68,
        latest_record_count: 5,
        previous_record_count: 3,
        status: 'checked',
        last_checked_at: '2026-05-11T13:00:00Z',
      },
    ])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
      expect(screen.getByText('eye drops')).toBeInTheDocument()
      expect(screen.getAllByText('RecallRadar').length).toBeGreaterThan(0)
      expect(screen.getByText('checked')).toBeInTheDocument()
      expect(screen.getByText('74')).toBeInTheDocument()
      expect(screen.getByText('68')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
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

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText('No saved monitors yet. Create one above to start the monitoring workflow.'),
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
      expect(screen.getByText('metformin')).toBeInTheDocument()
      expect(screen.getAllByText('DrugSignal').length).toBeGreaterThan(0)
    })
  })

  it('shows validation error for short name or query', async () => {
    vi.mocked(listSavedMonitors).mockResolvedValue([])

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(
        screen.getByText('No saved monitors yet. Create one above to start the monitoring workflow.'),
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

  it('runs a saved monitor check and updates latest and previous row values', async () => {
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

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Eye drops monitor')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Run Check' }))

    await waitFor(() => {
      expect(runSavedMonitor).toHaveBeenCalledWith('monitor-1')
      expect(screen.getByText('checked')).toBeInTheDocument()
      expect(screen.getByText('88')).toBeInTheDocument()
      expect(screen.getByText('70')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
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

    render(<SavedMonitorsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'View Audit' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'View Audit' }))

    expect(window.location.search).toContain('page=audit')
    expect(window.location.search).toContain('audit_id=33333333-3333-3333-3333-333333333333')
    expect(dispatchSpy).toHaveBeenCalled()

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
    })

    fireEvent.click(screen.getByRole('button', { name: 'Run Check' }))

    await waitFor(() => {
      expect(screen.getByText('Unable to run saved monitor check.')).toBeInTheDocument()
    })
  })
})
