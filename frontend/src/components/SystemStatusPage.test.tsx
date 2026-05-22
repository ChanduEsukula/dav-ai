import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getSources } from '../api/sources'
import { getDataQuality, getSystemStatus } from '../api/systemStatus'
import SystemStatusPage from './SystemStatusPage'

vi.mock('../api/systemStatus', () => ({
  getSystemStatus: vi.fn(),
  getDataQuality: vi.fn(),
}))

vi.mock('../api/sources', () => ({
  getSources: vi.fn(),
}))

describe('SystemStatusPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders system status, source freshness, and data quality details', async () => {
    vi.mocked(getSystemStatus).mockResolvedValue({
      status: 'ok',
      app: 'Dav AI API',
      version: '0.1.0',
      database: {
        configured: true,
        audit_readable: true,
      },
      sources: {
        registered_count: 2,
        available: true,
      },
      modules: ['RecallRadar', 'DrugSignal'],
    })

    vi.mocked(getDataQuality).mockResolvedValue({
      status: 'ok',
      database_configured: true,
      audit_readable: true,
      source_registry_count: 2,
      recent_audit_count: 3,
      upstream_status_counts: {
        success: 2,
        empty: 1,
        error: 0,
      },
      latest_audit_event: {
        exists: true,
        audit_id: 'audit-123',
        module: 'DrugSignal',
        query: 'aspirin',
        upstream_status: 'success',
        record_count: 5,
        created_at: '2026-05-21T10:00:00Z',
      },
    })

    vi.mocked(getSources).mockResolvedValue({
      count: 2,
      sources: [
        {
          source_id: 'openfda_drug_enforcement',
          source_name: 'openFDA Drug Enforcement API',
          endpoint: 'https://api.fda.gov/drug/enforcement.json',
          module: 'RecallRadar',
          description: 'Drug recall enforcement records from openFDA.',
          update_cadence: 'Source-dependent FDA updates',
          freshness_status: 'fresh',
          freshness_label: 'Fresh',
          last_successful_retrieval_at: '2026-05-19T18:44:03.346774+00:00',
          last_attempted_retrieval_at: '2026-05-19T18:44:03.346774+00:00',
          last_record_count: 5,
          last_error_message: null,
          freshness_reason:
            'Last successful retrieval was 2 day(s) ago, within the 14-day MVP freshness window.',
        },
        {
          source_id: 'openfda_drug_event',
          source_name: 'openFDA Drug Event API',
          endpoint: 'https://api.fda.gov/drug/event.json',
          module: 'DrugSignal',
          description: 'FAERS adverse-event and medication-error reports from openFDA.',
          update_cadence: 'Periodic FDA FAERS updates',
          freshness_status: 'fresh',
          freshness_label: 'Fresh',
          last_successful_retrieval_at: '2026-05-19T20:50:59.164248+00:00',
          last_attempted_retrieval_at: '2026-05-19T20:50:59.164248+00:00',
          last_record_count: 5,
          last_error_message: null,
          freshness_reason:
            'Last successful retrieval was 1 day(s) ago, within the 14-day MVP freshness window.',
        },
      ],
    })

    render(<SystemStatusPage />)

    expect(screen.getByText('Checking system status...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('System Status')).toBeInTheDocument()
      expect(screen.getByText('API: ok')).toBeInTheDocument()
    })

    expect(screen.getByText('Database configured: Yes')).toBeInTheDocument()
    expect(screen.getByText('Audit readable: Yes')).toBeInTheDocument()
    expect(screen.getByText('Sources: 2')).toBeInTheDocument()

    expect(screen.getByText('Fresh sources: 2')).toBeInTheDocument()
    expect(screen.getByText('Delayed: 0')).toBeInTheDocument()
    expect(screen.getAllByText('Error: 0')).toHaveLength(2)
    expect(screen.getByText('Unknown: 0')).toBeInTheDocument()

    expect(screen.getByText('Recent audits: 3')).toBeInTheDocument()
    expect(screen.getByText('Success: 2')).toBeInTheDocument()
    expect(screen.getByText('Empty: 1')).toBeInTheDocument()
    expect(screen.getByText('Latest query')).toBeInTheDocument()
    expect(screen.getByText('aspirin')).toBeInTheDocument()
    expect(screen.getByText('audit-123')).toBeInTheDocument()

    expect(screen.getByText('openFDA Drug Enforcement API')).toBeInTheDocument()
    expect(screen.getByText('openFDA Drug Event API')).toBeInTheDocument()
    expect(screen.getAllByText('Fresh')).toHaveLength(2)
  })

  it('renders an error message when status cannot be loaded', async () => {
    vi.mocked(getSystemStatus).mockRejectedValue(new Error('network error'))

    vi.mocked(getDataQuality).mockResolvedValue({
      status: 'ok',
      database_configured: true,
      audit_readable: true,
      source_registry_count: 2,
      recent_audit_count: 0,
      upstream_status_counts: {
        success: 0,
        empty: 0,
        error: 0,
      },
      latest_audit_event: {
        exists: false,
      },
    })

    vi.mocked(getSources).mockResolvedValue({
      count: 0,
      sources: [],
    })

    render(<SystemStatusPage />)

    await waitFor(() => {
      expect(
        screen.getByText('Unable to load system status. Please check the backend deployment.'),
      ).toBeInTheDocument()
    })
  })
})
