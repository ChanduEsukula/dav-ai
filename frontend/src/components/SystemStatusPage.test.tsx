import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import SystemStatusPage from './SystemStatusPage'
import { getDataQuality, getSystemStatus } from '../api/systemStatus'

vi.mock('../api/systemStatus', () => ({
  getSystemStatus: vi.fn(),
  getDataQuality: vi.fn(),
}))

describe('SystemStatusPage', () => {
  it('renders system status and data quality details', async () => {
    vi.mocked(getSystemStatus).mockResolvedValue({
      status: 'ok',
      app: 'MedTrek AI API',
      version: '0.1.0',
      database: {
        configured: true,
        audit_readable: true,
      },
      sources: {
        registered_count: 2,
        available: true,
      },
      modules: ['RecallRadar', 'DrugSignal', 'Sources', 'Audit History'],
    })

    vi.mocked(getDataQuality).mockResolvedValue({
      status: 'ok',
      database_configured: true,
      audit_readable: true,
      source_registry_count: 2,
      recent_audit_count: 25,
      upstream_status_counts: {
        success: 13,
        empty: 12,
        error: 0,
      },
      latest_audit_event: {
        exists: true,
        audit_id: 'audit-123',
        module: 'RecallRadar',
        query: 'eye drops',
        upstream_status: 'success',
        record_count: 5,
        created_at: '2026-05-08 14:46:12.823375+00:00',
      },
    })

    render(<SystemStatusPage />)

    expect(screen.getByText('Checking system status...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('System Status')).toBeInTheDocument()
      expect(screen.getByText('API: ok')).toBeInTheDocument()
      expect(screen.getByText('Database configured: Yes')).toBeInTheDocument()
      expect(screen.getByText('Audit readable: Yes')).toBeInTheDocument()
      expect(screen.getByText('MedTrek AI API')).toBeInTheDocument()
      expect(screen.getByText('RecallRadar, DrugSignal, Sources, Audit History')).toBeInTheDocument()
      expect(screen.getByText('Data Quality')).toBeInTheDocument()
      expect(screen.getByText('Recent audits: 25')).toBeInTheDocument()
      expect(screen.getByText('Success: 13')).toBeInTheDocument()
      expect(screen.getByText('Empty: 12')).toBeInTheDocument()
      expect(screen.getByText('Error: 0')).toBeInTheDocument()
      expect(screen.getByText('audit-123')).toBeInTheDocument()
      expect(screen.getByText('eye drops')).toBeInTheDocument()
    })
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

    render(<SystemStatusPage />)

    await waitFor(() => {
      expect(
        screen.getByText('Unable to load system status. Please check the backend deployment.'),
      ).toBeInTheDocument()
    })
  })
})
